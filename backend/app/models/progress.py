"""
Progress tracking model
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Progress(Base):
    """User progress per subject"""
    __tablename__ = "progress"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_quizzes: Mapped[int] = mapped_column(Integer, default=0)
    avg_quiz_score: Mapped[float] = mapped_column(Float, default=0.0)
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0)
    
    weak_topics: Mapped[dict] = mapped_column(JSON, nullable=True)  # ["topic1", "topic2"]
    strong_topics: Mapped[dict] = mapped_column(JSON, nullable=True)  # ["topic1", "topic2"]
    
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="progress")
    subject = relationship("Subject", back_populates="progress")
