"""
Add these classes to backend/app/models/teacher.py at the end (before the last line)
"""


class ConversationTurn(Base):
    """
    Each message in a teaching dialogue
    Tracks the back-and-forth between AI teacher and student
    """
    __tablename__ = "conversation_turns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    turn_index = Column(Integer, nullable=False)  # Order in conversation
    speaker = Column(String, nullable=False)  # "ai" or "student"
    message = Column(Text, nullable=False)
    
    concept_tag = Column(String, nullable=True)  # Which concept being discussed
    pdf_references = Column(JSON, nullable=True)  # Which PDF chunks were used
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ConceptMastery(Base):
    """
    Tracks student's understanding of each concept in a module
    Updated throughout the conversation
    """
    __tablename__ = "concept_mastery"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("teacher_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    concept = Column(String, nullable=False)
    mastery_score = Column(Float, nullable=False, default=0.0)  # 0-1
    attempts = Column(Integer, nullable=False, default=0)
    
    last_assessed = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Unique constraint: one row per user per module per concept
    __table_args__ = (
        UniqueConstraint('module_id', 'user_id', 'concept', name='unique_concept_mastery'),
    )
