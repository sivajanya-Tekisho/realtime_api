import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import QdrantService

async def main():
    load_dotenv()
    
    qdrant = QdrantService()
    
    # Sample data to add
    knowledge_base = [
        {
            "text": "vocalQ.ai is an advanced AI-powered voice assistant platform that uses real-time STT, VAD, and LLMs to provide seamless customer support.",
            "metadata": {"category": "general", "source": "official_docs"}
        },
        {
            "text": "Our office hours are Monday through Friday, 9:00 AM to 6:00 PM EST. We are closed on weekends and public holidays.",
            "metadata": {"category": "hours", "source": "official_docs"}
        },
        {
            "text": "To reset your password, go to the login page, click 'Forgot Password', and follow the instructions sent to your registered email.",
            "metadata": {"category": "support", "source": "faq"}
        },
        {
            "text": "vocalQ supports multiple languages including English, Spanish, French, and German for both speech recognition and synthesis.",
            "metadata": {"category": "languages", "source": "features"}
        }
    ]
    
    print(f"--- Adding {len(knowledge_base)} documents to Qdrant ---")
    for item in knowledge_base:
        print(f"Adding: {item['text'][:50]}...")
        await qdrant.add_document(item["text"], item["metadata"])
    
    print("--- Done! ---")

if __name__ == "__main__":
    asyncio.run(main())
