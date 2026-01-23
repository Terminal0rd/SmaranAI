"""
Progress tracking service
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.progress import Progress
from app.models.session import Session
from app.models.quiz import QuizAttempt
from app.models.subject import Subject


class ProgressService:
    """Service for tracking learning progress"""
    
    async def get_subject_progress(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str
    ) -> Optional[Progress]:
        """Get progress for a specific subject"""
        result = await db.execute(
            select(Progress)
            .where(Progress.user_id == user_id, Progress.subject_id == subject_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_progress(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[dict]:
        """Get progress for all subjects"""
        result = await db.execute(
            select(Progress, Subject)
            .join(Subject, Progress.subject_id == Subject.id)
            .where(Progress.user_id == user_id)
        )
        
        progress_list = []
        for progress, subject in result.all():
            progress_list.append({
                'subject_id': subject.id,
                'subject_name': subject.name,
                'total_sessions': progress.total_sessions,
                'total_quizzes': progress.total_quizzes,
                'avg_quiz_score': progress.avg_quiz_score,
                'time_spent_minutes': progress.time_spent_minutes,
                'weak_topics': progress.weak_topics or [],
                'strong_topics': progress.strong_topics or [],
                'last_activity': progress.last_activity
            })
        
        return progress_list
    
    async def get_dashboard_data(
        self,
        db: AsyncSession,
        user_id: str
    ) -> dict:
        """Get complete dashboard data"""
        # Get all progress
        progress_list = await self.get_all_progress(db, user_id)
        
        # Calculate totals
        total_sessions = sum(p['total_sessions'] for p in progress_list)
        total_quizzes = sum(p['total_quizzes'] for p in progress_list)
        total_time = sum(p['time_spent_minutes'] for p in progress_list)
        
        # Average score
        scores = [p['avg_quiz_score'] for p in progress_list if p['total_quizzes'] > 0]
        overall_avg_score = sum(scores) / len(scores) if scores else 0
        
        # Aggregate weak topics
        all_weak = []
        for p in progress_list:
            all_weak.extend(p['weak_topics'])
        weak_topics = list(set(all_weak))[:10]
        
        # Get quiz history
        result = await db.execute(
            select(QuizAttempt)
            .where(QuizAttempt.user_id == user_id, QuizAttempt.completed_at.isnot(None))
            .order_by(QuizAttempt.completed_at.desc())
            .limit(10)
        )
        quiz_history = [
            {'date': q.completed_at.isoformat(), 'score': q.score}
            for q in result.scalars().all()
        ]
        
        # Get recent activity
        result = await db.execute(
            select(Session, Subject)
            .join(Subject, Session.subject_id == Subject.id)
            .where(Session.user_id == user_id)
            .order_by(Session.updated_at.desc())
            .limit(5)
        )
        recent_activity = [
            {
                'type': 'session',
                'title': session.title or f"{subject.name} Session",
                'date': session.updated_at.isoformat(),
                'subject': subject.name
            }
            for session, subject in result.all()
        ]
        
        # Recommended topics (from weak topics + new topics)
        result = await db.execute(select(Subject).limit(5))
        subjects = result.scalars().all()
        recommended = weak_topics[:3] + [s.name for s in subjects[:2]]
        
        return {
            'progress': {
                'total_subjects': len(progress_list),
                'total_sessions': total_sessions,
                'total_quizzes': total_quizzes,
                'overall_avg_score': overall_avg_score,
                'total_time_spent_minutes': total_time,
                'subjects': progress_list
            },
            'weak_topics': weak_topics,
            'recommended_topics': recommended[:5],
            'recent_activity': recent_activity,
            'quiz_scores_history': quiz_history
        }
    
    async def update_session_progress(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str,
        time_spent: int = 1
    ):
        """Update progress after session activity"""
        result = await db.execute(
            select(Progress)
            .where(Progress.user_id == user_id, Progress.subject_id == subject_id)
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = Progress(
                user_id=user_id,
                subject_id=subject_id,
                total_sessions=0
            )
            db.add(progress)
        
        progress.time_spent_minutes += time_spent
        progress.last_activity = datetime.utcnow()
        
        await db.commit()
    
    async def increment_session_count(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str
    ):
        """Increment session count for a subject"""
        result = await db.execute(
            select(Progress)
            .where(Progress.user_id == user_id, Progress.subject_id == subject_id)
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = Progress(
                user_id=user_id,
                subject_id=subject_id,
                total_sessions=1
            )
            db.add(progress)
        else:
            progress.total_sessions += 1
        
        progress.last_activity = datetime.utcnow()
        await db.commit()


# Global instance
progress_service = ProgressService()
