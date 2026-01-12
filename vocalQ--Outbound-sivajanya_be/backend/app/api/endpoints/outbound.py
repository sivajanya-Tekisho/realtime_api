from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from pydantic import BaseModel
from app.services.outbound_service import OutboundService

router = APIRouter()
outbound_service = OutboundService()

class OutboundRequest(BaseModel):
    phone_numbers: List[str]

class OutboundStatusResponse(BaseModel):
    is_running: bool
    current_call_sid: str | None
    queue_size: int

@router.post("/start")
async def start_outbound_calls(request: OutboundRequest):
    """Start a new batch of outbound calls."""
    if not request.phone_numbers:
        raise HTTPException(status_code=400, detail="Phone numbers list is empty")
    
    await outbound_service.add_to_queue(request.phone_numbers)
    return {"message": f"Added {len(request.phone_numbers)} numbers to queue and started processing."}

@router.get("/status", response_model=OutboundStatusResponse)
async def get_outbound_status():
    """Get the current status of the outbound calling process."""
    return {
        "is_running": outbound_service.is_running,
        "current_call_sid": outbound_service.current_call_sid,
        "queue_size": outbound_service.queue.qsize()
    }
