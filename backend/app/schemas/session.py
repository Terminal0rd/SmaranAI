"""
Session and message schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class MessageBase(BaseModel):
    """Base message schema"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class MessageCreate(BaseModel):
    """Create message (user input)"""
    content: str = Field(..., min_length=1, max_length=4000)


class MessageResponse(MessageBase):
    """Message response schema"""
    id: str
    formatted_content: Optional[str] = None
    sources_used: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    """Base session schema"""
    title: Optional[str] = Field(None, max_length=255)


class SessionCreate(BaseModel):
    """Create session schema"""
    subject_id: str
    title: Optional[str] = Field(None, max_length=255)


class SessionUpdate(BaseModel):
    """Update session schema"""
    title: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class SessionResponse(SessionBase):
    """Session response schema"""
    id: str
    user_id: str
    subject_id: str
    summary: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionWithMessages(SessionResponse):
    """Session with messages"""
    messages: List[MessageResponse] = []


class ConceptResponse(BaseModel):
    """Extracted concept response"""
    id: str
    concept_name: str
    explanation: Optional[str] = None
    mastery_score: float
    created_at: datetime

    class Config:
        from_attributes = True
