"""
Chat schemas for AI tutor interaction
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Chat request schema"""
    session_id: str
    message: str = Field(..., min_length=1, max_length=4000)


class SourceReference(BaseModel):
    """Source reference for RAG"""
    filename: str
    chunk_preview: str


class ChatResponse(BaseModel):
    """Chat response schema"""
    message_id: str
    content: str
    formatted_content: str
    sources: List[SourceReference] = []
    concepts_extracted: List[str] = []
    audio_url: Optional[str] = None  # NEW: Audio file URL for voice tutor mode


class YouTubeRecommendation(BaseModel):
    """YouTube recommendation"""
    title: str
    search_query: str
    search_url: str
