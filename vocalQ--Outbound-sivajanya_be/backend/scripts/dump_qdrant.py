import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.qdrant_service import QdrantService
from app.core.config import settings

async def main():
    qdrant = QdrantService()
    # Wait for the collection to be ensured
    await asyncio.sleep(3) 
    docs = await qdrant.list_documents()
    print(f"Total documents: {len(docs)}")
    for doc in docs:
        print(f"ID: {doc['id']}")
        print(f"Text: {doc['text']}")
        print(f"Metadata: {doc['metadata']}")
        print("-" * 40)
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())



