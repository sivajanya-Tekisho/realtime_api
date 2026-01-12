import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum

from app.db.base_class import Base

class CallStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class ParticipantRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Call(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    external_call_id = Column(String, index=True, nullable=True) # From Twilio/Provider
    caller_number = Column(String, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0) # In seconds
    status = Column(String, default=CallStatus.ACTIVE)
    language = Column(String, default="en-US")
    intent = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    data_fetched = Column(Boolean, default=False)
    
    turns = relationship("ConversationTurn", back_populates="call", cascade="all, delete-orphan")

class ConversationTurn(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    call_id = Column(UUID(as_uuid=True), ForeignKey("call.id"))
    role = Column(String, nullable=False) # user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    call = relationship("Call", back_populates="turns")
