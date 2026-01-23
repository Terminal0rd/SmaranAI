"""
Subject API routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])

# Default subjects for new users
DEFAULT_SUBJECTS = [
    {"name": "Mathematics", "icon": "📐", "description": "Numbers, algebra, calculus, and more"},
    {"name": "Physics", "icon": "⚛️", "description": "Study of matter, energy, and forces"},
    {"name": "Chemistry", "icon": "🧪", "description": "Elements, compounds, and reactions"},
    {"name": "Biology", "icon": "🧬", "description": "Study of living organisms"},
    {"name": "Computer Science", "icon": "💻", "description": "Programming, algorithms, and systems"},
    {"name": "History", "icon": "📜", "description": "Events and civilizations of the past"},
    {"name": "English", "icon": "📚", "description": "Language, literature, and writing"},
]


@router.get("", response_model=List[SubjectResponse])
async def get_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available subjects"""
    result = await db.execute(select(Subject).order_by(Subject.name))
    subjects = result.scalars().all()
    
    # Create default subjects if none exist
    if not subjects:
        for subj_data in DEFAULT_SUBJECTS:
            subject = Subject(**subj_data, is_default=True)
            db.add(subject)
        await db.commit()
        
        result = await db.execute(select(Subject).order_by(Subject.name))
        subjects = result.scalars().all()
    
    return [SubjectResponse.model_validate(s) for s in subjects]


@router.post("", response_model=SubjectResponse)
async def create_subject(
    subject_data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subject"""
    # Check if exists
    result = await db.execute(
        select(Subject).where(Subject.name == subject_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subject already exists")
    
    subject = Subject(**subject_data.model_dump())
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    
    return SubjectResponse.model_validate(subject)


@router.get("/recommended", response_model=List[SubjectResponse])
async def get_recommended_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recommended subjects based on user profile"""
    # Get all subjects first
    result = await db.execute(select(Subject))
    all_subjects = result.scalars().all()
    
    # Simple recommendation based on branch
    recommendations = []
    branch = (current_user.branch_specialization or "").lower()
    
    priority_map = {
        "computer": ["Computer Science", "Mathematics"],
        "science": ["Physics", "Chemistry", "Biology", "Mathematics"],
        "commerce": ["Mathematics", "English"],
        "arts": ["History", "English"],
    }
    
    priority_subjects = []
    for key, subjects in priority_map.items():
        if key in branch:
            priority_subjects = subjects
            break
    
    # Sort by priority
    for subj in all_subjects:
        if subj.name in priority_subjects:
            recommendations.insert(0, subj)
        else:
            recommendations.append(subj)
    
    return [SubjectResponse.model_validate(s) for s in recommendations[:5]]


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific subject"""
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return SubjectResponse.model_validate(subject)
