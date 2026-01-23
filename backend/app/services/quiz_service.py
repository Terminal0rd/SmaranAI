"""
Quiz generation and scoring service
"""
import json
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.quiz import QuizAttempt, QuizQuestion
from app.models.session import Session, Message, SessionConcept
from app.models.progress import Progress
from app.services.llm_service import llm_service
from app.services.embedding_service import embedding_service


class QuizService:
    """Service for quiz generation and scoring"""
    
    async def generate_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        session_id: str,
        subject_id: str,
        num_questions: int = 5,
        question_types: List[str] = None
    ) -> Tuple[QuizAttempt, List[QuizQuestion]]:
        """
        Generate a quiz based on session content
        
        Args:
            db: Database session
            user_id: User ID
            session_id: Session ID
            subject_id: Subject ID
            num_questions: Number of questions
            question_types: Types of questions
            
        Returns:
            Tuple of (QuizAttempt, list of QuizQuestions)
        """
        if question_types is None:
            question_types = ["mcq", "true_false", "short_answer"]
        
        # Gather content for quiz generation
        content_parts = []
        
        # Get session messages
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id, Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        messages = result.scalars().all()
        
        for msg in messages:
            content_parts.append(msg.content[:1000])
        
        # Get session concepts
        result = await db.execute(
            select(SessionConcept)
            .where(SessionConcept.session_id == session_id)
        )
        concepts = result.scalars().all()
        
        for concept in concepts:
            content_parts.append(f"Concept: {concept.concept_name}")
            if concept.explanation:
                content_parts.append(concept.explanation[:500])
        
        # Get some RAG context
        rag_results = embedding_service.search(
            " ".join([c.concept_name for c in concepts[:3]]) if concepts else "general",
            top_k=3,
            subject_id=subject_id
        )
        
        for result in rag_results:
            content_parts.append(result['metadata']['content'][:500])
        
        content = "\n\n".join(content_parts)
        
        # Generate questions using LLM
        questions_json = await llm_service.generate_quiz_questions(
            content,
            num_questions,
            question_types
        )
        
        # Parse questions
        questions_data = self._parse_quiz_json(questions_json, num_questions)
        
        # Create quiz attempt
        attempt = QuizAttempt(
            user_id=user_id,
            session_id=session_id,
            subject_id=subject_id,
            total_questions=len(questions_data)
        )
        db.add(attempt)
        await db.flush()
        
        # Create question records
        questions = []
        for q_data in questions_data:
            question = QuizQuestion(
                attempt_id=attempt.id,
                question_type=q_data.get('type', 'mcq'),
                question_text=q_data.get('question', ''),
                options=q_data.get('options'),
                correct_answer=str(q_data.get('answer', '')),
                source_concept=q_data.get('concept')
            )
            db.add(question)
            questions.append(question)
        
        await db.commit()
        await db.refresh(attempt)
        
        return attempt, questions
    
    def _parse_quiz_json(self, json_str: str, expected_count: int) -> List[dict]:
        """Parse quiz JSON from LLM output"""
        # Try to extract JSON from response
        try:
            # Find JSON array in response
            start = json_str.find('[')
            end = json_str.rfind(']') + 1
            
            if start != -1 and end > start:
                json_str = json_str[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Fallback: create dummy questions
        return [
            {
                'type': 'mcq',
                'question': f'Sample question {i+1}?',
                'options': ['A) Option 1', 'B) Option 2', 'C) Option 3', 'D) Option 4'],
                'answer': 'A',
                'concept': 'General'
            }
            for i in range(expected_count)
        ]
    
    async def submit_quiz(
        self,
        db: AsyncSession,
        attempt_id: str,
        answers: List[dict]
    ) -> Tuple[QuizAttempt, List[str]]:
        """
        Score a quiz submission
        
        Args:
            db: Database session
            attempt_id: Quiz attempt ID
            answers: List of {question_id, answer}
            
        Returns:
            Tuple of (updated attempt, weak topics)
        """
        from datetime import datetime
        
        # Get attempt
        result = await db.execute(
            select(QuizAttempt).where(QuizAttempt.id == attempt_id)
        )
        attempt = result.scalar_one_or_none()
        
        if not attempt:
            raise ValueError("Quiz attempt not found")
        
        # Get questions
        result = await db.execute(
            select(QuizQuestion).where(QuizQuestion.attempt_id == attempt_id)
        )
        questions = {q.id: q for q in result.scalars().all()}
        
        # Score answers
        correct_count = 0
        weak_topics = set()
        
        for answer in answers:
            q_id = answer['question_id']
            user_answer = answer['answer']
            
            if q_id in questions:
                question = questions[q_id]
                question.user_answer = user_answer
                
                # Check answer (case-insensitive for text answers)
                is_correct = self._check_answer(
                    question.question_type,
                    question.correct_answer,
                    user_answer
                )
                question.is_correct = is_correct
                
                if is_correct:
                    correct_count += 1
                elif question.source_concept:
                    weak_topics.add(question.source_concept)
        
        # Update attempt
        attempt.correct_answers = correct_count
        attempt.score = (correct_count / attempt.total_questions) * 100 if attempt.total_questions > 0 else 0
        attempt.weak_topics_detected = list(weak_topics)
        attempt.completed_at = datetime.utcnow()
        
        # Update progress
        await self._update_progress(
            db,
            attempt.user_id,
            attempt.subject_id,
            attempt.score,
            list(weak_topics)
        )
        
        await db.commit()
        await db.refresh(attempt)
        
        return attempt, list(weak_topics)
    
    def _check_answer(
        self,
        question_type: str,
        correct: str,
        user: str
    ) -> bool:
        """Check if answer is correct"""
        if not user:
            return False
        
        correct = correct.strip().lower()
        user = user.strip().lower()
        
        if question_type == 'true_false':
            return correct == user
        elif question_type == 'mcq':
            # Accept letter only or full option
            return correct[0] == user[0] if user else False
        else:
            # Short answer: check if key words match
            correct_words = set(correct.split())
            user_words = set(user.split())
            overlap = len(correct_words & user_words) / len(correct_words) if correct_words else 0
            return overlap >= 0.6
    
    async def _update_progress(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str,
        score: float,
        weak_topics: List[str]
    ):
        """Update user progress after quiz"""
        result = await db.execute(
            select(Progress)
            .where(Progress.user_id == user_id, Progress.subject_id == subject_id)
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = Progress(user_id=user_id, subject_id=subject_id)
            db.add(progress)
        
        # Update stats
        progress.total_quizzes += 1
        
        # Update average score (running average)
        old_total = progress.avg_quiz_score * (progress.total_quizzes - 1)
        progress.avg_quiz_score = (old_total + score) / progress.total_quizzes
        
        # Update weak topics
        current_weak = set(progress.weak_topics or [])
        current_weak.update(weak_topics)
        progress.weak_topics = list(current_weak)[:20]  # Limit to 20


# Global instance
quiz_service = QuizService()
