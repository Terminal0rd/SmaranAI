"""
Document schemas for PDF upload
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    id: str
    filename: str
    original_name: str
    file_size: int
    subject_id: str
    is_processed: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(DocumentUploadResponse):
    """Document with processing status"""
    chunks_count: int = 0


class DocumentListResponse(BaseModel):
    """List of documents"""
    documents: List[DocumentResponse]
    total: int


class ProcessingStatusResponse(BaseModel):
    """Document processing status"""
    document_id: str
    is_processed: bool
    chunks_count: int
    status_message: str
