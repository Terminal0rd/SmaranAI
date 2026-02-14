"""
Preparation Model
Database schema for storing user preparation generations
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Preparation(Base):
    """Store user's preparation generations with full content"""
    __tablename__ = "preparations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Request parameters
    subject = Column(String(200), nullable=False, index=True)
    university = Column(String(200), nullable=False)
    exam_type = Column(String(50), nullable=False)
    exam_date = Column(String(50), nullable=True)
    
    # Generated content (stored as JSON for flexibility)
    content = Column(JSON, nullable=False, default={})
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preparations")
    
    def __repr__(self):
        return f"<Preparation(id={self.id}, subject={self.subject}, user_id={self.user_id})>"
