"""
Document Ingestion Service for RAG (Retrieval-Augmented Generation)
Handles document upload, parsing, chunking, embedding, and storage in Qdrant.
"""

import logging
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import PyPDF2
from docx import Document as DocxDocument
import re

from app.services.llm_service import LLMService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

class DocumentIngestionService:
    """Service for ingesting documents into the RAG knowledge base."""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.qdrant_service = QdrantService()
        self.chunk_size = 1000  # characters per chunk
        self.chunk_overlap = 200  # overlap between chunks
        self.knowledge_base_dir = Path(__file__).parent.parent.parent / "knowledge_base" / "uploaded"
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        
    async def ingest_document(self, file_path: str, file_name: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Ingest a document into the knowledge base.
        """
        try:
            logger.info(f"Ingesting document: {file_name}")
            
            # Parse document
            text = self._parse_document(file_path, file_name)
            if not text:
                raise ValueError(f"Could not extract text from {file_name}")
            
            # Chunk the document
            chunks = self._chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks from {file_name}")
            
            # Create embeddings and store
            doc_id = self._generate_doc_id(file_name)
            
            # Prepare metadata
            doc_metadata = {
                "source": file_name,
                "doc_id": doc_id,
                "category": "uploaded_document",
                **(metadata or {})
            }
            
            # Store chunks in Qdrant
            point_ids = await self._store_chunks(chunks, doc_metadata)
            
            # Save original file
            saved_path = self._save_document(file_path, file_name, doc_id)
            
            result = {
                "success": True,
                "file_name": file_name,
                "doc_id": doc_id,
                "chunks_created": len(chunks),
                "points_stored": len(point_ids),
                "saved_path": str(saved_path),
                "message": f"Successfully ingested {file_name} with {len(chunks)} chunks"
            }
            
            logger.info(result["message"])
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting document {file_name}: {str(e)}")
            return {
                "success": False,
                "file_name": file_name,
                "error": str(e)
            }
    
    def _parse_document(self, file_path: str, file_name: str) -> str:
        """
        Parse document based on file type.
        Supports: PDF, TXT, DOCX
        """
        file_ext = Path(file_name).suffix.lower()
        
        try:
            if file_ext == ".pdf":
                return self._parse_pdf(file_path)
            elif file_ext == ".txt":
                return self._parse_txt(file_path)
            elif file_ext == ".docx":
                return self._parse_docx(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            logger.error(f"Error parsing {file_name}: {str(e)}")
            raise
    
    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = []
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise
    
    def _parse_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = DocxDocument(file_path)
            text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text.append(para.text)
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error parsing DOCX: {str(e)}")
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        Uses sentence-aware chunking when possible.
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If not at end of text, try to split at sentence boundary
            if end < len(text):
                # Look for sentence boundary (., !, ?) within last 100 chars
                last_sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end)
                )
                
                if last_sentence_end > start:
                    end = last_sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start >= len(text) - 1:
                break
        
        return chunks
    
    async def _store_chunks(self, chunks: List[str], metadata: Dict) -> List[int]:
        """
        Embed and store chunks in Qdrant.
        """
        point_ids = []
        
        for idx, chunk in enumerate(chunks):
            try:
                # Generate embedding using Qdrant service
                embedding = await self.qdrant_service.get_embedding(chunk)
                
                # Create point data
                point_id = self._generate_point_id(metadata["doc_id"], idx)
                point_metadata = {
                    **metadata,
                    "chunk_index": idx,
                    "chunk_size": len(chunk),
                    "text_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
                }
                
                # Store in Qdrant
                await self.qdrant_service.add_point(
                    point_id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "metadata": point_metadata
                    }
                )
                
                point_ids.append(point_id)
                
            except Exception as e:
                logger.error(f"Error embedding chunk {idx}: {str(e)}")
                continue
        
        return point_ids
    
    def _save_document(self, file_path: str, file_name: str, doc_id: str) -> Path:
        """Save uploaded document to knowledge base folder."""
        try:
            # Create subdirectory by doc_id
            doc_dir = self.knowledge_base_dir / doc_id
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            saved_path = doc_dir / file_name
            with open(file_path, 'rb') as src:
                with open(saved_path, 'wb') as dst:
                    dst.write(src.read())
            
            return saved_path
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise
    
    def _generate_doc_id(self, file_name: str) -> str:
        """Generate unique document ID based on file name and current time."""
        import time
        content = f"{file_name}-{time.time()}".encode()
        return hashlib.md5(content).hexdigest()[:12]
    
    def _generate_point_id(self, doc_id: str, chunk_idx: int) -> int:
        """Generate unique point ID for chunk."""
        # Convert doc_id hex to int and add chunk index
        return int(doc_id, 16) + chunk_idx
    
    async def delete_document(self, doc_id: str) -> Dict:
        """
        Delete a document and all its chunks from the knowledge base.
        """
        try:
            # Delete chunks from Qdrant (by filtering on doc_id in metadata)
            await self.qdrant_service.delete_by_metadata("doc_id", doc_id)
            
            # Delete saved document files
            doc_dir = self.knowledge_base_dir / doc_id
            if doc_dir.exists():
                import shutil
                shutil.rmtree(doc_dir)
            
            return {
                "success": True,
                "doc_id": doc_id,
                "message": f"Successfully deleted document {doc_id}"
            }
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    def list_documents(self) -> List[Dict]:
        """List all ingested documents."""
        documents = []
        try:
            if self.knowledge_base_dir.exists():
                for doc_dir in self.knowledge_base_dir.iterdir():
                    if doc_dir.is_dir():
                        files = list(doc_dir.glob("*"))
                        if files:
                            documents.append({
                                "doc_id": doc_dir.name,
                                "files": [f.name for f in files],
                                "file_count": len(files)
                            })
            return documents
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
