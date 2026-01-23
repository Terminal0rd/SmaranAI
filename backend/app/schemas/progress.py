"""
Progress schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SubjectProgressResponse(BaseModel):
    """Progress for a single subject"""
    subject_id: str
    subject_name: str
    total_sessions: int
    total_quizzes: int
    avg_quiz_score: float
    time_spent_minutes: int
    weak_topics: List[str] = []
    strong_topics: List[str] = []
    last_activity: datetime

    class Config:
        from_attributes = True


class OverallProgressResponse(BaseModel):
    """Overall user progress"""
    total_subjects: int
    total_sessions: int
    total_quizzes: int
    overall_avg_score: float
    total_time_spent_minutes: int
    subjects: List[SubjectProgressResponse]


class DashboardDataResponse(BaseModel):
    """Dashboard data for charts"""
    progress: OverallProgressResponse
    weak_topics: List[str]
    recommended_topics: List[str]
    recent_activity: List[dict]
    quiz_scores_history: List[dict]  # [{date, score}]
