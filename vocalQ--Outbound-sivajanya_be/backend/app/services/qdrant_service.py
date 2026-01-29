import logging
import sys
import asyncio
import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.core.config import settings

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self):
        print("--- Initializing Async QdrantService ---")
        sys.stdout.flush()
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = "knowledge_base"
        self.vector_size = 768 # Gemini text-embedding-004

        # Check collection on startup
        asyncio.create_task(self._ensure_collection())
        print("--- Async QdrantService Initialized ---")
        sys.stdout.flush()

    async def _ensure_collection(self):
        """Ensure Qdrant collection exists and has correct dimensions."""
        try:
            collections_response = await self.client.get_collections()
            collections = collections_response.collections
            exists = any(c.name == self.collection_name for c in collections)
            
            recreate = False
            if exists:
                # Check dimensions
                info = await self.client.get_collection(self.collection_name)
                current_size = info.config.params.vectors.size
                if current_size != self.vector_size:
                    print(f"--- Qdrant Dimension Mismatch: {current_size} vs {self.vector_size}. Recreating... ---")
                    sys.stdout.flush()
                    recreate = True
            
            if not exists or recreate:
                if recreate:
                    await self.client.delete_collection(self.collection_name)
                
                logger.info(f"Creating collection: {self.collection_name}")
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")

    async def get_embedding(self, text: str) -> list:
        """Generate embedding using Gemini"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                return data["embedding"]["values"]
            except Exception as e:
                logger.error(f"Gemini Embedding failed: {e}")
                return []

    async def search(self, query_text: str, limit: int = 3):
        """Search for relevant documents in Qdrant (Async)."""
        try:
            # Generate embedding for query
            query_vector = await self.get_embedding(query_text)
            
            if not query_vector:
                return []

            # Use query_points method
            search_result = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True
            )
            
            results = [hit.payload.get("text", "") for hit in search_result.points]
            logger.info(f"Qdrant search for '{query_text[:50]}': found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}", exc_info=True)
            return []

    async def add_document(self, text: str, metadata: dict = None):
        """Add a document to the knowledge base (Async)."""
        try:
            vector = await self.get_embedding(text)
            if not vector:
                raise ValueError("Failed to generate embedding")

            import uuid
            response = await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={"text": text, **(metadata or {})}
                    )
                ],
                wait=True
            )
            logger.info(f"Document added to Qdrant: {text[:50]}... (Response: {response})")
        except Exception as e:
            logger.error(f"Failed to add document to Qdrant: {e}", exc_info=True)
            raise

    async def list_documents(self):
        """List all documents in the knowledge base."""
        try:
            # Scroll to get all points
            points, _ = await self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True,
                with_vectors=False
            )
            return [
                {
                    "id": p.id,
                    "text": p.payload.get("text", ""),
                    "metadata": {k: v for k, v in p.payload.items() if k != "text"}
                }
                for p in points
            ]
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    async def delete_document(self, doc_id: str):
        """Delete a document from the knowledge base."""
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[doc_id],
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    async def clear_knowledge_base(self):
        """Delete and recreate the knowledge base collection."""
        try:
            await self.client.delete_collection(self.collection_name)
            await self._ensure_collection()
            logger.info("Knowledge base collection cleared and recreated")
            return True
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return False
