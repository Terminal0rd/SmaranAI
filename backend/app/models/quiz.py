"""
Quiz models
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Float, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class QuizAttempt(Base):
    """Quiz attempt tracking"""
    __tablename__ = "quiz_attempts"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    
    score: Mapped[float] = mapped_column(Float, default=0.0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    
    weak_topics_detected: Mapped[dict] = mapped_column(JSON, nullable=True)  # ["topic1", "topic2"]
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    session = relationship("Session", back_populates="quiz_attempts")
    questions = relationship("QuizQuestion", back_populates="attempt", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """Individual quiz question"""
    __tablename__ = "quiz_questions"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("quiz_attempts.id"), nullable=False)
    
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)  # mcq, true_false, short_answer
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSON, nullable=True)  # For MCQ: ["A", "B", "C", "D"]
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
    user_answer: Mapped[str] = mapped_column(String(500), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=True)
    
    source_concept: Mapped[str] = mapped_column(String(255), nullable=True)  # Which concept this tests
    
    # Relationships
    attempt = relationship("QuizAttempt", back_populates="questions")
