"""
Teacher Mode Schemas
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Enums
class ModuleStatus(str):
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"


class ModuleLevel(str):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LessonPhase(str):
    TEACH = "teach"
    CHECK = "check"
    RETEACH = "reteach"


class CardType(str):
    CONCEPT = "concept"
    FORMULA = "formula"
    MISTAKE = "mistake"
    EXAMPLE = "example"


# ===== Roadmap Schemas =====

class RoadmapCreate(BaseModel):
    """Request to create a new teacher roadmap"""
    subject: str = Field(..., min_length=1, max_length=255)
    goal: Optional[str] = Field(None, max_length=500, description="exam / understanding / projects")


class ModuleObjective(BaseModel):
    """Single learning objective"""
    text: str
    order: int


class ModuleTopic(BaseModel):
    """Single lesson topic"""
    text: str
    order: int


class ModuleResponse(BaseModel):
    """Module data in roadmap"""
    id: str
    module_index: int
    title: str
    level: str
    objectives: List[str]
    topics: List[str]
    prerequisites: Optional[List[int]] = None
    estimated_minutes: int
    status: str
    mastery_score: float

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    """Complete roadmap response"""
    id: str
    subject: str
    goal: Optional[str]
    total_modules: int
    completed_modules: int
    overall_progress: float
    modules: List[ModuleResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoadmapListResponse(BaseModel):
    """Simplified roadmap for list view"""
    id: str
    subject: str
    goal: Optional[str]
    total_modules: int
    completed_modules: int
    overall_progress: float
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Module/Lesson Schemas =====

class TeachContentResponse(BaseModel):
    """Structured teaching content"""
    module_title: str
    sections: List[Dict[str, Any]]  # [{"type": "definition", "title": "...", "content": "..."}]
    summary: str


class CheckQuestion(BaseModel):
    """Single check question"""
    question_id: Optional[str] = None
    question_type: str  # "mcq" | "short_answer"
    question_text: str
    options: Optional[List[str]] = None  # For MCQ


class CheckQuestionsResponse(BaseModel):
    """Generated check questions"""
    module_id: str
    questions: List[CheckQuestion]


class CheckAnswer(BaseModel):
    """Student's answer to a question"""
    question_id: str
    answer: str


class CheckSubmission(BaseModel):
    """Submit check answers"""
    answers: List[CheckAnswer]


class QuestionGrading(BaseModel):
    """Grading for individual question"""
    question_id: str
    correct: bool
    feedback: Optional[str] = None


class CheckResultResponse(BaseModel):
    """Result of check phase"""
    score: float  # 0.0 to 1.0
    passed: bool
    weak_topics: Optional[List[str]] = None
    grading_details: List[QuestionGrading]
    next_action: str  # "next_module" | "reteach"


class ReteachRequest(BaseModel):
    """Request reteach for weak topics"""
    weak_topics: List[str]


class ReteachContentResponse(BaseModel):
    """Simplified reteach content"""
    weak_topics: List[str]
    explanations: List[Dict[str, str]]  # [{"topic": "...", "explanation": "..."}]
    practice_questions: List[CheckQuestion]


# ===== Memory Cards Schemas =====

class MemoryCardResponse(BaseModel):
    """Single memory card"""
    id: str
    card_type: str
    front_text: str
    back_text: str
    display_order: int

    class Config:
        from_attributes = True


class MemoryCardsResponse(BaseModel):
    """All memory cards for a module"""
    module_id: str
    module_title: str
    cards: List[MemoryCardResponse]


# ===== Module Detail Schema =====

class ModuleDetailResponse(BaseModel):
    """Complete module with current state"""
    id: str
    module_index: int
    title: str
    level: str
    objectives: List[str]
    topics: List[str]
    prerequisites: Optional[List[int]] = None
    estimated_minutes: int
    status: str
    mastery_score: float
    current_phase: Optional[str] = None  # From lesson_state
    check_attempts: int = 0
    can_retry: bool = True

    class Config:
        from_attributes = True


# ===== Teach Chat Schemas =====

class TeachChatRequest(BaseModel):
    """Request for interactive Q&A during teaching"""
    message: str = Field(..., min_length=1, max_length=1000)


class TeachChatResponse(BaseModel):
    """AI response to student question during teaching"""
    response: str
