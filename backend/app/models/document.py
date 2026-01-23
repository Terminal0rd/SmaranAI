"""
Document models for PDF uploads and RAG
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Document(Base):
    """Uploaded PDF document"""
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    uploader_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # Stored filename
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Original upload name
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = relationship("User", back_populates="documents")
    subject = relationship("Subject", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Chunked text from document for RAG"""
    __tablename__ = "document_chunks"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[str] = mapped_column(String(100), nullable=True)  # Reference in vector store
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
