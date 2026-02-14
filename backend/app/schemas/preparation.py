"""
Preparation Mode Schemas
Request/Response models for AI Semester Preparation Engine
"""
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class PreparationRequest(BaseModel):
    """Request to generate semester preparation"""
    subject: str
    university: str
    exam_type: Optional[str] = "Regular"  # Regular/Backlog/Competitive
    exam_date: Optional[str] = None  # YYYY-MM-DD format
    use_rag: Optional[bool] = True  # Use RAG if documents available


class SyllabusUnit(BaseModel):
    """Single unit in syllabus"""
    unit_number: int
    unit_title: str
    topics: List[str]
    estimated_hours: int


class SmartNote(BaseModel):
    """Smart notes for a topic"""
    topic: str
    explanation: str
    key_definitions: List[str]
    formulas: List[str]
    important_points: List[str]


class Question(BaseModel):
    """Practice question"""
    question: str
    marks: int
    unit: str
    difficulty: str  # Easy/Medium/Hard
    hint: Optional[str] = None


class PredictedQuestion(BaseModel):
    """Predicted important question"""
    question: str
    marks: int
    probability: str  # High/Medium/Low
    reason: str
    unit: str


class MockTestSection(BaseModel):
    """Section of mock test"""
    section_name: str  # Section A/B/C
    instructions: str
    questions: List[Question]
    total_marks: int


class VivaQuestion(BaseModel):
    """Viva/oral question"""
    question: str
    expected_answer: str
    unit: str


class PPTSlide(BaseModel):
    """PowerPoint slide content"""
    slide_number: int
    title: str
    bullet_points: List[str]
    diagram_suggestion: Optional[str] = None


class StudyPlanDay(BaseModel):
    """Single day in study plan"""
    day_number: int
    date: Optional[str] = None
    tasks: List[str]
    topics_to_cover: List[str]
    revision: bool
    mock_test: bool


class PreparationResponse(BaseModel):
    """Complete preparation package"""
    preparation_id: str
    subject: str
    university: str
    exam_type: str
    exam_date: Optional[str] = None
    
    # 1. Syllabus
    syllabus: List[SyllabusUnit]
    
    # 2. Smart Notes
    notes: List[SmartNote]
    
    # 3. 5-Mark Questions
    five_mark_questions: List[Question]
    
    # 4. 10-Mark Questions
    ten_mark_questions: List[Question]
    
    # 5. Predicted Questions
    predicted_questions: List[PredictedQuestion]
    
    # 6. Mock Test
    mock_test: Dict[str, MockTestSection]  # sections: A, B, C
    
    # 7. Viva Questions
    viva_questions: List[VivaQuestion]
    
    # 8. PPT Content
    ppt_content: List[PPTSlide]
    
    # 9. Study Plan
    study_plan: List[StudyPlanDay]
    
    created_at: datetime
    generated_with_rag: bool
