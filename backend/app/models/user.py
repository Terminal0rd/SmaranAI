"""
User model
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile fields
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    class_standard: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g., "12th", "B.Tech 3rd Year"
    branch_specialization: Mapped[str] = mapped_column(String(100), nullable=True)  # e.g., "Computer Science"
    learning_goal: Mapped[str] = mapped_column(String(50), nullable=True)  # exam, understanding, projects
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploader", cascade="all, delete-orphan")
    mindmap_nodes = relationship("MindMapNode", back_populates="user", cascade="all, delete-orphan")
    preparations = relationship("Preparation", back_populates="user", cascade="all, delete-orphan")

