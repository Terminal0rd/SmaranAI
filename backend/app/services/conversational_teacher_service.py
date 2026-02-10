"""
Conversational Teacher Service
Revolutionary dialogue-based teaching with RAG integration
"""

import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.teacher import (
    TeacherModule, ConversationTurn, ConceptMastery,
    ModuleStatus
)
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class ConversationalTeacherService:
    """
    Socratic AI teacher that guides students through concepts via dialogue
    Uses RAG to pull from uploaded PDFs for accurate, contextual teaching
    """
    
    async def start_teaching(
        self,
        module_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Start a teaching session for a module
        Returns the AI's opening message
        """
        # Get module
        module_result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = module_result.scalar_one()
        
        # Get concepts from module topics
        concepts = module.topics  # ["Variables", "Data Types", "Operators"]
        
        # Initialize concept mastery tracking
        for concept in concepts:
            existing = await db.execute(
                select(ConceptMastery).where(
                    ConceptMastery.module_id == module_id,
                    ConceptMastery.user_id == user_id,
                    ConceptMastery.concept == concept
                )
            )
            if not existing.scalar_one_or_none():
                mastery = ConceptMastery(
                    module_id=module_id,
                    user_id=user_id,
                    concept=concept,
                    mastery_score=0.0
                )
                db.add(mastery)
        
        await db.commit()
        
        # Get first concept
        first_concept = concepts[0]
        
        # Retrieve relevant content from PDFs
       pdf_context = await rag_service.search(
            query=f"{first_concept} in {module.title} explanation examples",
            user_id=user_id,
            top_k=5
        )
        
        context_str = "\n\n".join([chunk.get("text", "") for chunk in pdf_context])
        
        # Generate opening message
        prompt = f"""You are an AI tutor starting a 1-on-1 teaching session.

Module: {module.title}
First Topic: {first_concept}
Course Material: {context_str}

Your goal: Teach through Socratic dialogue. Start by:
1. Greeting the student warmly
2. Briefly explain what you'll cover today
3. Ask an opening question to gauge their prior knowledge about {first_concept}

Be conversational, friendly, and encouraging. Keep it under 100 words."""

        ai_message = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        # Save conversation turn
        turn = ConversationTurn(
            module_id=module_id,
            user_id=user_id,
            turn_index=0,
            speaker="ai",
            message=ai_message,
            concept_tag=first_concept,
            pdf_references=pdf_context
        )
        db.add(turn)
        await db.commit()
        
        return {
            "message": ai_message,
            "current_concept": first_concept,
            "progress": {
                "current": 0,
                "total": len(concepts),
                "concepts": concepts
            }
        }
    
    async def respond_to_student(
        self,
        module_id: str,
        user_id: str,
        student_message: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process student's response and generate next AI message
        Core of the conversational teaching loop
        """
        # Get module
        module_result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = module_result.scalar_one()
        
        # Get conversation history
        history_result = await db.execute(
            select(ConversationTurn)
            .where(
                ConversationTurn.module_id == module_id,
                ConversationTurn.user_id == user_id
            )
            .order_by(ConversationTurn.turn_index)
        )
        history = history_result.scalars().all()
        
        # Get current concept from last AI message
        current_concept = history[-1].concept_tag if history else module.topics[0]
        
        # Get concept mastery progress
        mastery_result = await db.execute(
            select(ConceptMastery).where(
                ConceptMastery.module_id == module_id,
                ConceptMastery.user_id == user_id
            )
        )
        masteries = {m.concept: m for m in mastery_result.scalars().all()}
        
        # Save student's message
        student_turn = ConversationTurn(
            module_id=module_id,
            user_id=user_id,
            turn_index=len(history),
            speaker="student",
            message=student_message,
            concept_tag=current_concept
        )
        db.add(student_turn)
        
        # Build conversation context
        conversation_context = "\n".join([
            f"{'AI' if turn.speaker == 'ai' else 'Student'}: {turn.message}"
            for turn in history[-10:]  # Last 10 turns for context
        ])
        conversation_context += f"\nStudent: {student_message}"
        
        # Assess understanding of current response
        understanding = await self._assess_understanding(
            student_message,
            current_concept,
            module.title,
            user_id,
            db
        )
        
        # Update mastery score
        current_mastery = masteries.get(current_concept)
        if current_mastery:
            current_mastery.mastery_score = understanding["score"]
            current_mastery.attempts += 1
            current_mastery.last_assessed = datetime.utcnow()
        
        # Decide next action
        concepts_list = module.topics
        current_index = concepts_list.index(current_concept)
        
        # Check if concept mastered (score >= 0.7)
        if understanding["score"] >= 0.7:
            # Move to next concept or finish
            if current_index + 1 < len(concepts_list):
                next_concept = concepts_list[current_index + 1]
                ai_response = await self._transition_to_next_concept(
                    current_concept,
                    next_concept,
                    student_message,
                    module.title,
                    user_id,
                    db
                )
                concept_tag = next_concept
                all_done = False
            else:
                # All concepts covered
                ai_response = await self._finish_teaching(
                    conversation_context,
                    module.title,
                    db
                )
                concept_tag = current_concept
                all_done = True
        else:
            # Continue teaching current concept
            ai_response = await self._continue_teaching(
                current_concept,
                student_message,
                conversation_context,
                understanding,
                module.title,
                user_id,
                db
            )
            concept_tag = current_concept
            all_done = False
        
        # Save AI response
        ai_turn = ConversationTurn(
            module_id=module_id,
            user_id=user_id,
            turn_index=len(history) + 1,
            speaker="ai",
            message=ai_response["message"],
            concept_tag=concept_tag,
            pdf_references=ai_response.get("pdf_refs")
        )
        db.add(ai_turn)
        await db.commit()
        
        # Calculate progress
        mastered_count = sum(1 for m in masteries.values() if m.mastery_score >= 0.7)
        
        return {
            "message": ai_response["message"],
            "current_concept": concept_tag,
            "all_concepts_done": all_done,
            "progress": {
                "current": mastered_count,
                "total": len(concepts_list),
                "concepts": concepts_list,
                "mastery_scores": {c: masteries[c].mastery_score for c in masteries}
            }
        }
    
    async def _assess_understanding(
        self,
        student_response: str,
        concept: str,
        module_title: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Assess how well student understands the concept from their response
        Returns score 0-1 and feedback
        """
        prompt = f"""Assess this student's understanding of "{concept}" in {module_title}.

Student's response: "{student_response}"

Rate 0.0 to 1.0:
- 0.0-0.3: Doesn't understand
- 0.4-0.6: Partial understanding
- 0.7-1.0: Good understanding

Return JSON: {{"score": 0.8, "feedback": "Shows good grasp of core principles"}}"""
        
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        try:
            result = json.loads(response.strip())
        except:
            result = {"score": 0.5, "feedback": "Moderate understanding"}
        
        return result
    
    async def _continue_teaching(
        self,
        concept: str,
        student_response: str,
        conversation_context: str,
        understanding: Dict,
        module_title: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Continue teaching current concept with different approach
        """
        # Get fresh PDFcontent
        pdf_context = await rag_service.search(
            query=f"{concept} {module_title} simple explanation examples",
            user_id=user_id,
            top_k=3
        )
        
        context_str = "\n\n".join([chunk.get("text", "") for chunk in pdf_context])
        
        prompt = f"""You're teaching "{concept}". The student's last response showed partial understanding.

Recent conversation:
{conversation_context[-500:]}

Course material:
{context_str}

Assessment: {understanding['feedback']}

Your turn: Help them understand better by:
1. Acknowledging their effort
2. Clarifying the concept with a simpler explanation or analogy
3. Give a concrete example from the course material
4. Ask a follow-up question to check understanding

Be encouraging. Keep under 150 words."""

        ai_message = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )
        
        return {
            "message": ai_message,
            "pdf_refs": pdf_context
        }
    
    async def _transition_to_next_concept(
        self,
        current_concept: str,
        next_concept: str,
        student_response: str,
        module_title: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Student mastered current concept, transition to next
        """
        # Get PDF context for next concept
        pdf_context = await rag_service.search(
            query=f"{next_concept} {module_title} introduction",
            user_id=user_id,
            top_k=5
        )
        
        context_str = "\n\n".join([chunk.get("text", "") for chunk in pdf_context])
        
        prompt = f"""The student just demonstrated good understanding of "{current_concept}".

Now transition to "{next_concept}":
1. Praise their grasp of {current_concept}
2. Briefly introduce {next_concept} and why it's important
3. Use course material: {context_str[:300]}
4. Ask an opening question about {next_concept}

Be enthusiastic and keep momentum. Under 120 words."""

        ai_message = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=350
        )
        
        return {
            "message": ai_message,
            "pdf_refs": pdf_context
        }
    
    async def _finish_teaching(
        self,
        conversation_context: str,
        module_title: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        All concepts covered, wrap up the lesson
        """
        prompt = f"""The student has mastered all concepts in {module_title}!

Conclude the lesson:
1. Congratulate them on completing the module
2. Briefly recap what they learned
3. Tell them they're ready for the assessment
4. Encourage them

Be warm and celebratory. Under 100 words."""

        ai_message = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=250
        )
        
        return {"message": ai_message}


conversational_teacher_service = ConversationalTeacherService()
