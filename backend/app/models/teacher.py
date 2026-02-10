"""
Teacher Mode Models
Separate learning system with AI-generated roadmaps and mastery gates
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ModuleStatus(str, enum.Enum):
    """Module completion status"""
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"


class ModuleLevel(str, enum.Enum):
    """Module difficulty level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LessonPhase(str, enum.Enum):
    """Current phase in lesson flow"""
    TEACH = "teach"
    CHECK = "check"
    RETEACH = "reteach"


class CardType(str, enum.Enum):
    """Memory card types"""
    CONCEPT = "concept"
    FORMULA = "formula"
    MISTAKE = "mistake"
    EXAMPLE = "example"


class TeacherRoadmap(Base):
    """
    AI-generated learning roadmap for a subject
    User can have multiple roadmaps for different subjects/goals
    """
    __tablename__ = "teacher_roadmaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    goal = Column(String(500), nullable=True)  # exam / understanding / projects
    total_modules = Column(Integer, nullable=False, default=0)
    completed_modules = Column(Integer, nullable=False, default=0)
    overall_progress = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    modules = relationship("TeacherModule", back_populates="roadmap", cascade="all, delete-orphan")
    user = relationship("User", back_populates="teacher_roadmaps")


class TeacherModule(Base):
    """
    Individual module in a learning roadmap
    Contains objectives, topics, and mastery tracking
    """
    __tablename__ = "teacher_modules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id = Column(String, ForeignKey("teacher_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    module_index = Column(Integer, nullable=False)  # Order in roadmap (0, 1, 2...)
    title = Column(String(500), nullable=False)
    level = Column(SQLEnum(ModuleLevel), nullable=False, default=ModuleLevel.BEGINNER)
    
    # Content as JSON
    objectives = Column(JSON, nullable=False)  # List of 3-6 learning objectives
    topics = Column(JSON, nullable=False)  # List of 3-8 lesson topics
    prerequisites = Column(JSON, nullable=True)  # Optional list of prerequisite module indices
    
    estimated_minutes = Column(Integer, nullable=False, default=30)
    status = Column(SQLEnum(ModuleStatus), nullable=False, default=ModuleStatus.LOCKED)
    mastery_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roadmap = relationship("TeacherRoadmap", back_populates="modules")
    lesson_state = relationship("TeacherLessonState", back_populates="module", uselist=False, cascade="all, delete-orphan")
    check_attempts = relationship("TeacherCheckAttempt", back_populates="module", cascade="all, delete-orphan")
    memory_cards = relationship("TeacherMemoryCard", back_populates="module", cascade="all, delete-orphan")


class TeacherLessonState(Base):
    """
    Tracks current state within a module lesson
    Manages teach → check → reteach flow
    """
    __tablename__ = "teacher_lesson_states"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    current_phase = Column(SQLEnum(LessonPhase), nullable=False, default=LessonPhase.TEACH)
    check_attempts = Column(Integer, nullable=False, default=0)  # Number of check attempts
    max_attempts = Column(Integer, nullable=False, default=2)
    
    # Generated content cache (to avoid regenerating)
    teach_content = Column(Text, nullable=True)
    reteach_content = Column(Text, nullable=True)
    check_questions = Column(JSON, nullable=True)  # Store generated questions
    
    # Topic progression tracking
    current_topic_index = Column(Integer, nullable=False, default=0)
    topics_completed = Column(JSON, nullable=True)  # List of completed topic indices
    
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    module = relationship("TeacherModule", back_populates="lesson_state")


class TeacherCheckAttempt(Base):
    """
    Records student's check phase attempts and results
    Used for analytics and reteach targeting
    """
    __tablename__ = "teacher_check_attempts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Attempt data
    questions = Column(JSON, nullable=False)  # List of questions asked
    answers = Column(JSON, nullable=False)  # Student's answers
    score = Column(Float, nullable=False)  # 0.0 to 1.0
    passed = Column(Integer, nullable=False, default=0)  # 0 = failed, 1 = passed
    
    # Grading details
    weak_topics = Column(JSON, nullable=True)  # Topics that need reteaching
    grading_details = Column(JSON, nullable=True)  # Per-question grading breakdown
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    module = relationship("TeacherModule", back_populates="check_attempts")
    user = relationship("User")


class TeacherMemoryCard(Base):
    """
    Retention cards generated after module mastery
    Key formulas, concepts, mistakes, examples
    """
    __tablename__ = "teacher_memory_cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    card_type = Column(SQLEnum(CardType), nullable=False)
    
    front_text = Column(Text, nullable=False)  # Question / Concept / Formula
    back_text = Column(Text, nullable=False)  # Answer / Explanation / Example
    
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    module = relationship("TeacherModule", back_populates="memory_cards")
