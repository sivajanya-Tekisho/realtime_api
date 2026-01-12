#!/usr/bin/env python
"""
Quick script to manage knowledge base articles.
Add your support documentation here.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import QdrantService

async def add_knowledge_base():
    """Add support articles to the knowledge base."""
    load_dotenv()
    
    qdrant = QdrantService()
    
    # Define your support knowledge base here
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
        },
        {
            "text": "Our platform uses Whisper for accurate speech-to-text transcription and OpenAI's TTS for natural sounding responses.",
            "metadata": {"category": "technical", "source": "technical_specs"}
        },
        {
            "text": "For billing inquiries, please contact our billing team at billing@vocalq.ai. Standard response time is 24-48 hours.",
            "metadata": {"category": "billing", "source": "contact_info"}
        },
        {
            "text": "We offer free trial access for 14 days with full feature access. No credit card required to get started.",
            "metadata": {"category": "pricing", "source": "pricing_page"}
        }
    ]
    
    print(f"Adding {len(knowledge_base)} articles to knowledge base...")
    for i, item in enumerate(knowledge_base, 1):
        print(f"[{i}/{len(knowledge_base)}] Adding: {item['text'][:60]}...")
        await qdrant.add_document(item["text"], item["metadata"])
    
    print("✓ Knowledge base populated successfully!")

if __name__ == "__main__":
    asyncio.run(add_knowledge_base())





