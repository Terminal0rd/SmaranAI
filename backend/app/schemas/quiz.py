"""
Quiz schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuizGenerateRequest(BaseModel):
    """Request to generate quiz"""
    session_id: str
    num_questions: int = Field(5, ge=1, le=20)
    question_types: List[str] = ["mcq", "true_false", "short_answer"]


class QuizQuestionResponse(BaseModel):
    """Quiz question for user"""
    id: str
    question_type: str
    question_text: str
    options: Optional[List[str]] = None  # For MCQ
    source_concept: Optional[str] = None

    class Config:
        from_attributes = True


class QuizAnswerSubmit(BaseModel):
    """Single answer submission"""
    question_id: str
    answer: str


class QuizSubmitRequest(BaseModel):
    """Submit quiz answers"""
    attempt_id: str
    answers: List[QuizAnswerSubmit]


class QuizQuestionResult(BaseModel):
    """Question result with correct answer"""
    question_id: str
    question_text: str
    options: Optional[List[str]] = None  # All MCQ options for display
    user_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    source_concept: Optional[str] = None


class QuizResultResponse(BaseModel):
    """Quiz result response"""
    attempt_id: str
    score: float
    total_questions: int
    correct_answers: int
    weak_topics: List[str]
    questions: List[QuizQuestionResult]


class QuizAttemptResponse(BaseModel):
    """Quiz attempt summary"""
    id: str
    subject_id: str
    session_id: Optional[str]
    score: float
    total_questions: int
    correct_answers: int
    weak_topics_detected: Optional[List[str]]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuizGenerateResponse(BaseModel):
    """Generated quiz response"""
    attempt_id: str
    questions: List[QuizQuestionResponse]
