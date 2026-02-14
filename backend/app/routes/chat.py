"""
Chat API routes (AI Tutor) - WITH STREAMING SUPPORT AND READ ALOUD
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import logging

from app.database import get_db
from app.models.session import Session, Message, SessionConcept
from app.models.subject import Subject
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, SourceReference, YouTubeRecommendation
from app.utils.security import get_current_user
from app.services.rag_service import rag_service
from app.services.mindmap_service import mindmap_service
from app.services.progress_service import progress_service
from app.services.streaming_service import stream_chat_completion
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service  # NEW: Voice Tutor Mode
from app.config import get_settings  # NEW: For voice tutor config

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger(__name__)
settings = get_settings()  # NEW: For voice tutor config


@router.post("/read-aloud/{message_id}")
async def read_aloud_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate audio for an existing message on-demand (Read Aloud button)
    Returns audio URL immediately
    """
    # Get the message
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Verify the message belongs to user's session
    session_result = await db.execute(
        select(Session).where(
            Session.id == message.session_id,
            Session.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate audio
    try:
        logger.info(f"Generating on-demand audio for message {message_id}")
        audio_url = await tts_service.generate_audio(
            text=message.content,
            message_id=str(message_id)
        )
        
        if not audio_url:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
        logger.info(f"Audio generated successfully: {audio_url}")
        
        return {
            "message_id": message_id,
            "audio_url": audio_url,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message and get AI tutor response WITH STREAMING"""
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
    await db.commit()
    
    # Get RAG context
    context, sources = await rag_service.get_context_for_query(
        request.message,
        subject_id=session.subject_id,
        top_k=2
    )
    
    # Get session summary
    session_summary = await rag_service.get_session_summary(db, session.id)
    
    # Limit context for GPU
    context_limited = (context[:500] + "...") if len(context) > 500 else context
    summary_limited = (session_summary[:200] + "...") if len(session_summary) > 200 else session_summary
    
    # Prepare messages
    system_prompt = "You are an AI tutor. Provide clear, concise educational responses with bullet points and examples."
    user_prompt = f"""CONTEXT: {context_limited if context_limited else "None"}

PREVIOUS: {summary_limited if summary_limited else "Start of session"}

QUESTION: {request.message}

Provide a clear, educational response."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Stream generator
    async def generate_stream():
        full_response = ""
        
        try:
            # Send initial metadata
            yield f"data: {json.dumps({'type': 'start', 'sources': sources})}\n\n"
            
            # Stream tokens
            async for token in stream_chat_completion(messages):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            # Extract concepts from full response
            try:
                concepts = await llm_service.extract_concepts(full_response)
            except:
                concepts = []
            
            # Save assistant message
            assistant_message = Message(
                session_id=session.id,
                role="assistant",
                content=full_response,
                formatted_content=full_response,
                sources_used=sources
            )
            db.add(assistant_message)
            
            # Save concepts
            for concept_name in concepts:
                result = await db.execute(
                    select(SessionConcept).where(
                        SessionConcept.session_id == session.id,
                        SessionConcept.concept_name == concept_name
                    )
                )
                if not result.scalar_one_or_none():
                    db.add(SessionConcept(
                        session_id=session.id,
                        concept_name=concept_name
                    ))
            
            # Add to mindmap
            if concepts:
                await mindmap_service.add_concepts(
                    db, current_user.id, session.subject_id, concepts
                )
            
            # Update progress
            from datetime import datetime
            session.updated_at = datetime.utcnow()
            await progress_service.update_session_progress(
                db, current_user.id, session.subject_id, time_spent=1
            )
            
            await db.commit()
            await db.refresh(assistant_message)
            
            # Send completion metadata
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id), 'concepts': concepts})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message and get AI tutor response (NON-STREAMING FALLBACK)"""
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
        logger.info(f"Adding {len(concepts)} concepts to mindmap for subject {session.subject_id}: {concepts}")
        
        added_nodes = await mindmap_service.add_concepts(
            db, current_user.id, session.subject_id, concepts
        )
        logger.info(f"Successfully added {len(added_nodes)} new nodes to mindmap")
    else:
        logger.warning("No concepts extracted - mindmap will not be updated")
    
    # Update session timestamp
    from datetime import datetime
    session.updated_at = datetime.utcnow()
    
    # Update progress (1 minute per message)
    await progress_service.update_session_progress(
        db, current_user.id, session.subject_id, time_spent=1
    )
    
    await db.commit()
    await db.refresh(assistant_message)
    
    # Generate audio if Voice Tutor Mode is enabled (NEW)
    audio_url = None
    if settings.enable_voice_tutor:
        try:
            logger.info(f"Generating audio for message {assistant_message.id}")
            audio_url = await tts_service.generate_audio(
                text=response,
                message_id=str(assistant_message.id)
            )
            if audio_url:
                logger.info(f"Audio generated successfully: {audio_url}")
            else:
                logger.warning("Audio generation returned None")
        except Exception as e:
            # Fail gracefully - don't break response if audio generation fails
            logger.error(f"Audio generation failed: {e}")
            audio_url = None
    
    return ChatResponse(
        message_id=assistant_message.id,
        content=response,
        formatted_content=formatted,
        sources=[SourceReference(**s) for s in sources],
        concepts_extracted=concepts,
        audio_url=audio_url  # NEW: Voice Tutor Mode
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
