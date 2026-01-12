import logging
from fastapi import APIRouter, HTTPException
from app.services.qdrant_service import QdrantService

from app.services.llm_service import LLMService

router = APIRouter()
logger = logging.getLogger(__name__)
qdrant_service = QdrantService()
llm_service = LLMService()

@router.get("/settings/greeting")
async def get_greeting():
    """Get the current AI greeting."""
    return {"greeting": LLMService.get_greeting()}

@router.post("/settings/greeting")
async def update_greeting(data: dict):
    """Update the AI greeting."""
    greeting = data.get("greeting")
    if not greeting:
        raise HTTPException(status_code=400, detail="Missing greeting text")
    LLMService.set_greeting(greeting)
    return {"status": "success", "greeting": greeting}
