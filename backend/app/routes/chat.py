"""
Chat API routes (AI Tutor)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.session import Session, Message, SessionConcept
from app.models.subject import Subject
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, SourceReference, YouTubeRecommendation
from app.utils.security import get_current_user
from app.services.rag_service import rag_service
from app.services.mindmap_service import mindmap_service
from app.services.progress_service import progress_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message and get AI tutor response"""
    # Get session
    result = await db.execute(
        select(Session).where(
            Session.id == request.session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    user_message = Message(
        session_id=session.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.flush()
    
    # Generate response using RAG
    try:
        response, formatted, sources, concepts = await rag_service.generate_response(
            db=db,
            session_id=session.id,
            subject_id=session.subject_id,
            question=request.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")
    
    # Save assistant message
    assistant_message = Message(
        session_id=session.id,
        role="assistant",
        content=response,
        formatted_content=formatted,
        sources_used=sources
    )
    db.add(assistant_message)
    
    # Save extracted concepts
    for concept_name in concepts:
        # Check if concept already exists
        result = await db.execute(
            select(SessionConcept).where(
                SessionConcept.session_id == session.id,
                SessionConcept.concept_name == concept_name
            )
        )
        if not result.scalar_one_or_none():
            concept = SessionConcept(
                session_id=session.id,
                concept_name=concept_name
            )
            db.add(concept)
    
    # Add concepts to mindmap
    if concepts:
        await mindmap_service.add_concepts(
            db, current_user.id, session.subject_id, concepts
        )
    
    # Update session timestamp
    from datetime import datetime
    session.updated_at = datetime.utcnow()
    
    # Update progress (1 minute per message)
    await progress_service.update_session_progress(
        db, current_user.id, session.subject_id, time_spent=1
    )
    
    await db.commit()
    await db.refresh(assistant_message)
    
    return ChatResponse(
        message_id=assistant_message.id,
        content=response,
        formatted_content=formatted,
        sources=[SourceReference(**s) for s in sources],
        concepts_extracted=concepts
    )


@router.get("/youtube-recommend", response_model=List[YouTubeRecommendation])
async def get_youtube_recommendations(
    topic: str,
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get YouTube video recommendations for a topic"""
    # Get subject name
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    try:
        recommendations = await rag_service.get_youtube_recommendations(
            topic, subject.name
        )
        return [YouTubeRecommendation(**r) for r in recommendations]
    except Exception as e:
        # Fallback recommendations
        search_query = f"{subject.name} {topic} tutorial"
        return [
            YouTubeRecommendation(
                title=f"{topic} Tutorial",
                search_query=search_query,
                search_url=f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            )
        ]
