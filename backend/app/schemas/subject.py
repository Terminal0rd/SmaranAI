"""
Subject schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubjectBase(BaseModel):
    """Base subject schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)


class SubjectCreate(SubjectBase):
    """Create subject schema"""
    pass


class SubjectUpdate(BaseModel):
    """Update subject schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)


class SubjectResponse(SubjectBase):
    """Subject response schema"""
    id: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True
