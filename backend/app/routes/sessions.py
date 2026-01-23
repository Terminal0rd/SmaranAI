"""
Session API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.session import Session, Message, SessionConcept
from app.models.subject import Subject
from app.models.user import User
from app.schemas.session import (
    SessionCreate, SessionResponse, SessionUpdate, 
    SessionWithMessages, MessageResponse, ConceptResponse
)
from app.utils.security import get_current_user
from app.services.progress_service import progress_service

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionResponse])
async def get_sessions(
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's sessions, optionally filtered by subject"""
    query = select(Session).where(Session.user_id == current_user.id)
    
    if subject_id:
        query = query.where(Session.subject_id == subject_id)
    
    query = query.order_by(Session.updated_at.desc())
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new learning session"""
    # Verify subject exists
    result = await db.execute(
        select(Subject).where(Subject.id == session_data.subject_id)
    )
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Create session
    session = Session(
        user_id=current_user.id,
        subject_id=session_data.subject_id,
        title=session_data.title or f"{subject.name} Session"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Update progress
    await progress_service.increment_session_count(
        db, current_user.id, session_data.subject_id
    )
    
    return SessionResponse.model_validate(session)


@router.get("/latest", response_model=Optional[SessionResponse])
async def get_latest_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the most recent active session"""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id, Session.is_active == True)
        .order_by(Session.updated_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return None
    
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a session with all messages"""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    # Build response dict manually to avoid lazy-loading issues
    return SessionWithMessages(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        title=session.title,
        summary=session.summary,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    updates: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a session"""
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse.model_validate(session)


@router.get("/{session_id}/concepts", response_model=List[ConceptResponse])
async def get_session_concepts(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get concepts extracted from a session"""
    # Verify session belongs to user
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get concepts
    result = await db.execute(
        select(SessionConcept)
        .where(SessionConcept.session_id == session_id)
        .order_by(SessionConcept.created_at)
    )
    concepts = result.scalars().all()
    
    return [ConceptResponse.model_validate(c) for c in concepts]
