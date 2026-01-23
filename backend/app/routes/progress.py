"""
Progress API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.progress import (
    SubjectProgressResponse, OverallProgressResponse, DashboardDataResponse
)
from app.utils.security import get_current_user
from app.services.progress_service import progress_service

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("", response_model=OverallProgressResponse)
async def get_overall_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall progress across all subjects"""
    progress_list = await progress_service.get_all_progress(db, current_user.id)
    
    total_sessions = sum(p['total_sessions'] for p in progress_list)
    total_quizzes = sum(p['total_quizzes'] for p in progress_list)
    total_time = sum(p['time_spent_minutes'] for p in progress_list)
    
    scores = [p['avg_quiz_score'] for p in progress_list if p['total_quizzes'] > 0]
    overall_avg = sum(scores) / len(scores) if scores else 0
    
    return OverallProgressResponse(
        total_subjects=len(progress_list),
        total_sessions=total_sessions,
        total_quizzes=total_quizzes,
        overall_avg_score=overall_avg,
        total_time_spent_minutes=total_time,
        subjects=[SubjectProgressResponse(**p) for p in progress_list]
    )


@router.get("/dashboard", response_model=DashboardDataResponse)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete dashboard data"""
    data = await progress_service.get_dashboard_data(db, current_user.id)
    
    # Convert nested objects
    progress = OverallProgressResponse(
        total_subjects=data['progress']['total_subjects'],
        total_sessions=data['progress']['total_sessions'],
        total_quizzes=data['progress']['total_quizzes'],
        overall_avg_score=data['progress']['overall_avg_score'],
        total_time_spent_minutes=data['progress']['total_time_spent_minutes'],
        subjects=[SubjectProgressResponse(**p) for p in data['progress']['subjects']]
    )
    
    return DashboardDataResponse(
        progress=progress,
        weak_topics=data['weak_topics'],
        recommended_topics=data['recommended_topics'],
        recent_activity=data['recent_activity'],
        quiz_scores_history=data['quiz_scores_history']
    )


@router.get("/{subject_id}", response_model=SubjectProgressResponse)
async def get_subject_progress(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress for a specific subject"""
    from sqlalchemy import select
    from app.models.subject import Subject
    
    # Get subject
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    progress = await progress_service.get_subject_progress(
        db, current_user.id, subject_id
    )
    
    if not progress:
        # Return empty progress
        return SubjectProgressResponse(
            subject_id=subject_id,
            subject_name=subject.name,
            total_sessions=0,
            total_quizzes=0,
            avg_quiz_score=0.0,
            time_spent_minutes=0,
            weak_topics=[],
            strong_topics=[],
            last_activity=subject.created_at
        )
    
    return SubjectProgressResponse(
        subject_id=subject_id,
        subject_name=subject.name,
        total_sessions=progress.total_sessions,
        total_quizzes=progress.total_quizzes,
        avg_quiz_score=progress.avg_quiz_score,
        time_spent_minutes=progress.time_spent_minutes,
        weak_topics=progress.weak_topics or [],
        strong_topics=progress.strong_topics or [],
        last_activity=progress.last_activity
    )
