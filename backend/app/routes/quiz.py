"""
Quiz API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.quiz import QuizAttempt, QuizQuestion
from app.models.user import User
from app.schemas.quiz import (
    QuizGenerateRequest, QuizGenerateResponse, QuizQuestionResponse,
    QuizSubmitRequest, QuizResultResponse, QuizQuestionResult, QuizAttemptResponse
)
from app.utils.security import get_current_user
from app.services.quiz_service import quiz_service
from app.services.mindmap_service import mindmap_service

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new quiz based on session content"""
    from app.models.session import Session
    
    # Verify session
    result = await db.execute(
        select(Session).where(
            Session.id == request.session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        attempt, questions = await quiz_service.generate_quiz(
            db=db,
            user_id=current_user.id,
            session_id=request.session_id,
            subject_id=session.subject_id,
            num_questions=request.num_questions,
            question_types=request.question_types
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")
    
    return QuizGenerateResponse(
        attempt_id=attempt.id,
        questions=[
            QuizQuestionResponse(
                id=q.id,
                question_type=q.question_type,
                question_text=q.question_text,
                options=q.options,
                source_concept=q.source_concept
            )
            for q in questions
        ]
    )


@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz(
    request: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit quiz answers and get results"""
    # Verify attempt belongs to user
    result = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == request.attempt_id,
            QuizAttempt.user_id == current_user.id
        )
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    
    if attempt.completed_at:
        raise HTTPException(status_code=400, detail="Quiz already submitted")
    
    # Submit and score
    answers = [{"question_id": a.question_id, "answer": a.answer} for a in request.answers]
    
    try:
        attempt, weak_topics = await quiz_service.submit_quiz(
            db, request.attempt_id, answers
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Update mindmap with weak topics
    if weak_topics:
        await mindmap_service.mark_weak_from_quiz(
            db, current_user.id, attempt.subject_id, weak_topics
        )
    
    # Get questions with results
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.attempt_id == attempt.id)
    )
    questions = result.scalars().all()
    
    return QuizResultResponse(
        attempt_id=attempt.id,
        score=attempt.score,
        total_questions=attempt.total_questions,
        correct_answers=attempt.correct_answers,
        weak_topics=weak_topics,
        questions=[
            QuizQuestionResult(
                question_id=q.id,
                question_text=q.question_text,
                options=q.options,
                user_answer=q.user_answer,
                correct_answer=q.correct_answer,
                is_correct=q.is_correct or False,
                source_concept=q.source_concept
            )
            for q in questions
        ]
    )


@router.get("/history", response_model=List[QuizAttemptResponse])
async def get_quiz_history(
    subject_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quiz history"""
    query = select(QuizAttempt).where(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.completed_at.isnot(None)
    )
    
    if subject_id:
        query = query.where(QuizAttempt.subject_id == subject_id)
    
    query = query.order_by(QuizAttempt.completed_at.desc()).limit(20)
    result = await db.execute(query)
    attempts = result.scalars().all()
    
    return [QuizAttemptResponse.model_validate(a) for a in attempts]


@router.get("/{attempt_id}", response_model=QuizResultResponse)
async def get_quiz_result(
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific quiz result"""
    result = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == current_user.id
        )
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    
    # Get questions
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.attempt_id == attempt_id)
    )
    questions = result.scalars().all()
    
    return QuizResultResponse(
        attempt_id=attempt.id,
        score=attempt.score,
        total_questions=attempt.total_questions,
        correct_answers=attempt.correct_answers,
        weak_topics=attempt.weak_topics_detected or [],
        questions=[
            QuizQuestionResult(
                question_id=q.id,
                question_text=q.question_text,
                options=q.options,
                user_answer=q.user_answer,
                correct_answer=q.correct_answer,
                is_correct=q.is_correct or False,
                source_concept=q.source_concept
            )
            for q in questions
        ]
    )
