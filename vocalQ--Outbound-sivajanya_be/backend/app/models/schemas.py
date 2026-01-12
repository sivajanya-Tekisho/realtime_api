from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid

class CallCreate(BaseModel):
    caller_number: str
    start_time: str # ISO string
    call_status: str = "active"
    language: str = "en-US"

class CallUpdate(BaseModel):
    end_time: Optional[str] = None
    call_duration: Optional[int] = None
    call_status: Optional[str] = None
    intent: Optional[str] = None
    
class SummaryCreate(BaseModel):
    call_id: str
    summary_text: str

class CallSchema(BaseModel):
    call_id: uuid.UUID
    caller_number: str
    start_time: datetime
    end_time: Optional[datetime]
    call_duration: Optional[int]
    language: Optional[str]
    intent: Optional[str]
    call_status: str
    created_at: datetime
