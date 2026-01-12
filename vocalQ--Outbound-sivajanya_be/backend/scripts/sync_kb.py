import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.qdrant_service import QdrantService
from app.services.document_ingestion_service import DocumentIngestionService

async def main():
    print("--- Starting Knowledge Base Cleanup and Sync ---")
    
    qdrant = QdrantService()
    doc_ingestion = DocumentIngestionService()
    
    # 1. Clear Qdrant collection
    print("Clearing Qdrant collection...")
    await qdrant.clear_knowledge_base()
    
    # 2. Sync with FS
    uploaded_dir = Path(__file__).parent.parent / "knowledge_base" / "uploaded"
    if not uploaded_dir.exists():
        print(f"Uploaded directory not found: {uploaded_dir}")
        return

    print(f"Scanning {uploaded_dir} for documents to re-ingest...")
    
    # Process files in root uploaded directory
    for file_path in uploaded_dir.glob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [".pdf", ".txt", ".docx"]:
            print(f"Re-ingesting: {file_path.name}")
            result = await doc_ingestion.ingest_document(
                file_path=str(file_path),
                file_name=file_path.name
            )
            if result["success"]:
                print(f"Successfully re-ingested {file_path.name}")
            else:
                print(f"Failed to re-ingest {file_path.name}: {result.get('error')}")

    # Process subdirectories if any
    for doc_dir in uploaded_dir.iterdir():
        if doc_dir.is_dir():
            for file_path in doc_dir.glob("*"):
                if file_path.suffix.lower() in [".pdf", ".txt", ".docx"]:
                    print(f"Re-ingesting: {file_path.name}")
                    result = await doc_ingestion.ingest_document(
                        file_path=str(file_path),
                        file_name=file_path.name
                    )
                    if result["success"]:
                        print(f"Successfully re-ingested {file_path.name}")
                    else:
                        print(f"Failed to re-ingest {file_path.name}: {result.get('error')}")

    print("--- Cleanup and Sync Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
