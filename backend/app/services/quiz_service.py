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
        
        # Gather content for quiz generation (SIMPLIFIED to prevent timeout)
        content_parts = []
        
        # Get only the 2 most recent session messages (reduced from 5)
        result = await db.execute(
            select( Message)
            .where(Message.session_id == session_id, Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .limit(2)  # Reduced
        )
        messages = result.scalars().all()
        
        for msg in messages:
            content_parts.append(msg.content[:500])  # Reduced from 1000
        
        # Get session concepts (just names)
        result = await db.execute(
            select(SessionConcept)
            .where(SessionConcept.session_id == session_id)
            .limit(5)  # Limit concepts
        )
        concepts = result.scalars().all()
        
        concept_names = [c.concept_name for c in concepts]
        if concept_names:
            content_parts.append("Key Topics: " + ", ".join(concept_names))
        
        # Skip RAG search to speed up (commented out)
        # rag_results = embedding_service.search(...)
        
        content = "\n\n".join(content_parts)
        
        # Limit total content length to prevent timeout
        if len(content) > 2000:
            content = content[:2000]
        
        # Generate questions using LLM (with fallback if timeout)
        questions_data = []
        try:
            questions_json = await llm_service.generate_quiz_questions(
                content,
                num_questions,
                question_types
            )
            # Parse questions
            questions_data = self._parse_quiz_json(questions_json, num_questions)
        except Exception as e:
            # Fallback: create simple questions from content
            import logging
            logging.warning(f"LLM quiz generation failed: {e}. Using fallback.")
            questions_data = self._create_fallback_questions(content, num_questions, concepts)
        
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
    
    def _create_fallback_questions(self, content: str, num_questions: int, concepts) -> List[dict]:
        """Create simple quiz questions when LLM fails"""
        questions = []
        
        # Extract some sentences from content
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20][:num_questions*2]
        
        for i in range(min(num_questions, len(sentences))):
            concept_name = concepts[i % len(concepts)].concept_name if concepts else "General"
            
            if i % 3 == 0:  # MCQ
                questions.append({
                    'type': 'mcq',
                    'question': f"What is the main idea about {concept_name}?",
                    'options': [
                        f'A) {sentences[i][:50] if i < len(sentences) else "Option A"}...',
                        'B) A different concept',
                        'C) Not related',
                        'D) None of the above'
                    ],
                    'answer': 'A',
                    'concept': concept_name
                })
            elif i % 3 == 1:  # True/False
                questions.append({
                    'type': 'true_false',
                    'question': f"True or False: {concept_name} is an important concept in this topic.",
                    'answer': 'True',
                    'concept': concept_name
                })
            else:  # Short answer
                questions.append({
                    'type': 'short_answer',
                    'question': f"Explain {concept_name} in one sentence.",
                    'answer': concept_name,
                    'concept': concept_name
                })
        
        return questions if questions else self._parse_quiz_json("", num_questions)
    
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
