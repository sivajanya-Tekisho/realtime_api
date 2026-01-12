import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())
                                                     
from app.services.qdrant_service import QdrantService
                                                      
async def main():
    qdrant = QdrantService()
    await asyncio.sleep(2)
    docs = await qdrant.list_documents()
    
    wrong_text = "Monday through Friday, 9:00 AM to 6:00 PM EST"
    doc_to_delete = None
    
    for doc in docs:
        if wrong_text in doc['text']:
            doc_to_delete = doc['id']
            print(f"Found document to delete: {doc_to_delete}")
            print(f"Content: {doc['text'][:100]}...")
            break
            
    if doc_to_delete:
        await qdrant.delete_document(doc_to_delete)
        print(f"Successfully deleted document: {doc_to_delete}")
    else:
        print("Wrong document not found.")

if __name__ == "__main__":
    asyncio.run(main())
