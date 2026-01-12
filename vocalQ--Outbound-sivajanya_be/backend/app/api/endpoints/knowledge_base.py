"""
Knowledge Base Management Endpoints
Handles document upload, deletion, and listing.
"""

import logging
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional

from app.services.document_ingestion_service import DocumentIngestionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/knowledge", tags=["knowledge-base"])

# Initialize service
doc_ingestion = DocumentIngestionService()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload a document to the knowledge base.
    
    Supported formats: PDF, TXT, DOCX
    
    The document will be automatically:
    - Parsed
    - Chunked (with overlap)
    - Embedded using OpenAI embeddings
    - Stored in Qdrant vector database
    
    Args:
        file: Document file to upload
        category: Optional category for the document
        description: Optional description of the document
        
    Returns:
        Ingestion results
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    allowed_extensions = {".pdf", ".txt", ".docx"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Prepare metadata
        metadata = {}
        if category:
            metadata["category"] = category
        if description:
            metadata["description"] = description
        
        # Ingest document
        result = await doc_ingestion.ingest_document(
            file_path=temp_path,
            file_name=file.filename,
            metadata=metadata
        )
        
        return JSONResponse(content=result, status_code=200 if result["success"] else 400)
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

@router.get("/list")
async def list_documents():
    """
    List all ingested documents in the knowledge base.
    
    Returns:
        List of documents with their metadata
    """
    try:
        documents = doc_ingestion.list_documents()
        return JSONResponse(
            content={
                "success": True,
                "count": len(documents),
                "documents": documents
            }
        )
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document and all its chunks from the knowledge base.
    
    Args:
        doc_id: Document ID to delete
        
    Returns:
        Deletion result
    """
    try:
        result = await doc_ingestion.delete_document(doc_id)
        status_code = 200 if result["success"] else 400
        return JSONResponse(content=result, status_code=status_code)
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/info")
async def knowledge_base_info():
    """
    Get information about the knowledge base.
    
    Returns:
        Knowledge base statistics
    """
    try:
        documents = doc_ingestion.list_documents()
        total_files = sum(doc["file_count"] for doc in documents)
        
        return JSONResponse(
            content={
                "status": "operational",
                "total_documents": len(documents),
                "total_files": total_files,
                "supported_formats": ["pdf", "txt", "docx"],
                "chunk_size": doc_ingestion.chunk_size,
                "chunk_overlap": doc_ingestion.chunk_overlap,
                "embedding_model": "OpenAI text-embedding-3-small",
                "vector_database": "Qdrant"
            }
        )
    except Exception as e:
        logger.error(f"Error getting KB info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting KB info: {str(e)}")
