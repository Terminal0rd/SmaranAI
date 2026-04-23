"""
AI Semester Preparation Service
Generates comprehensive exam preparation materials using LLM with parallel async calls
"""
import json
import logging
import asyncio
import re
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.schemas.preparation import *

logger = logging.getLogger(__name__)


class PreparationService:
    """Service for generating complete semester preparation using parallel async calls"""
    
    async def generate_preparation(
        self,
        subject: str,
        university: str,
        exam_type: str,
        exam_date: str | None,
        db: AsyncSession,
        use_rag: bool = True
    ) -> Dict:
        """
        Generate initial preparation with only syllabus (fast initial load)
        Other sections generated on-demand
        
        Returns structured dict matching PreparationResponse schema
        """
        logger.info(f"Generating initial preparation for {subject} at {university}")
        
        # Check if RAG context available (OPTIMIZED: top 3, max 1500 chars)
        rag_context = ""
        
        if use_rag:
            try:
                context, sources = await rag_service.get_context_for_query(
                    f"{subject} syllabus topics concepts",
                    subject_id=None,
                    top_k=3  # REDUCED: Only top 3 docs
                )
                if context.strip():
                    # LIMIT: Max 1500 characters total
                    rag_context = f"\n\nKNOWLEDGE BASE:\n{context[:1500]}"
                    logger.info(f"Using RAG context: {len(rag_context)} chars from {len(sources)} sources")
            except Exception as e:
                logger.warning(f"RAG not available: {e}")
        
        # Generate ONLY syllabus for fast initial response
        logger.info("Generating syllabus (fast initial load)...")
        syllabus_data = {"syllabus": []}
        
        try:
            syllabus_data = await self._generate_syllabus(subject, university, exam_type, rag_context)
        except Exception as e:
            logger.error(f"Syllabus generation failed: {e}")
        
        # Build response with only syllabus populated
        preparation_id = f"prep_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            "preparation_id": preparation_id,
            "subject": subject,
            "university": university,
            "exam_type": exam_type,
            "exam_date": exam_date,
            "syllabus": syllabus_data.get("syllabus", []),
            "notes": [],  # Empty - generate on-demand
            "five_mark_questions": [],  # Empty - generate on-demand
            "ten_mark_questions": [],  # Empty - generate on-demand
            "predicted_questions": [],  # Empty - generate on-demand
            "mock_test": {},  # Empty - generate on-demand
            "viva_questions": [],  # Empty - generate on-demand
            "ppt_content": [],  # Empty - generate on-demand
            "study_plan": [],  # Empty - generate on-demand
            "created_at": datetime.utcnow(),
            "generated_with_rag": bool(rag_context)
        }
        
        logger.info(f"Initial preparation (syllabus only) generated: {preparation_id}")
        return result
    
    async def generate_section(
        self,
        section: str,
        subject: str,
        university: str,
        exam_type: str,
        exam_date: str | None,
        db: AsyncSession,
        use_rag: bool = True
    ) -> Dict:
        """
        Generate a specific section on-demand
        
        Args:
            section: Section name (notes, questions, mock_viva, ppt_plan)
            
        Returns:
            Dict with generated section data
        """
        logger.info(f"Generating section '{section}' for {subject}")
        
        # Get RAG context if needed (OPTIMIZED: top 3, max 1500 chars)
        rag_context = ""
        if use_rag and section in ["notes", "syllabus"]:
            try:
                context, sources = await rag_service.get_context_for_query(
                    f"{subject} syllabus topics concepts",
                    subject_id=None,
                    top_k=3  # REDUCED: Only top 3 docs
                )
                if context.strip():
                    # LIMIT: Max 1500 characters total
                    rag_context = f"\n\nKNOWLEDGE BASE:\n{context[:1500]}"
                    logger.info(f"RAG context: {len(rag_context)} chars")
            except Exception as e:
                logger.warning(f"RAG not available: {e}")
        
        # Generate requested section
        try:
            if section == "notes":
                return await self._generate_notes(subject, university, rag_context)
            elif section == "questions":
                return await self._generate_questions(subject, university, exam_type)
            elif section == "mock_viva":
                return await self._generate_mock_and_viva(subject, university, exam_type)
            elif section == "ppt_plan":
                return await self._generate_ppt_and_plan(subject, university, exam_date)
            else:
                logger.error(f"Unknown section: {section}")
                return {}
        except Exception as e:
            logger.error(f"Section '{section}' generation failed: {e}")
            raise Exception(f"Failed to generate {section}: {str(e)}")
    
    # ===== PARALLEL GENERATION METHODS =====
    
    async def _generate_syllabus(self, subject: str, university: str, exam_type: str, rag_context: str) -> Dict:
        """Generate syllabus breakdown"""
        logger.info("Generating syllabus...")
        
        prompt = f"""Generate a semester SYLLABUS for {subject} at {university} ({exam_type} exam).{rag_context}

Return ONLY valid JSON with this structure:
{{
  "syllabus": [
    {{
      "unit_number": 1,
      "unit_title": "Unit Name",
      "topics": ["Topic 1", "Topic 2", "Topic 3"],
      "estimated_hours": 8
    }}
  ]
}}

Generate 4-5 units. Each unit should have 3-5 topics."""
        
        response = await self._call_llm(prompt, max_tokens=600)  # REDUCED for speed
        return self._safe_json_parse(response, {"syllabus": []})
    
    async def _generate_notes(self, subject: str, university: str, rag_context: str) -> Dict:
        """Generate smart notes"""
        logger.info("Generating notes...")
        
        prompt = f"""Generate SMART NOTES for top 5 topics in {subject} ({university}).{rag_context}

Return ONLY valid JSON:
{{
  "notes": [
    {{
      "topic": "Topic Name",
      "explanation": "Clear 2-3 paragraph explanation",
      "key_definitions": ["Def 1", "Def 2"],
      "formulas": ["Formula 1"],
      "important_points": ["Point 1", "Point 2"]
    }}
  ]
}}

Generate 5 detailed topic notes."""
        
        # INCREASED: Notes need more tokens for detailed explanations
        response = await self._call_llm(prompt, max_tokens=1000, timeout=180)
        return self._safe_json_parse(response, {"notes": []})
    
    async def _generate_questions(self, subject: str, university: str, exam_type: str) -> Dict:
        """Generate practice questions"""
        logger.info("Generating questions...")
        
        prompt = f"""Generate PRACTICE QUESTIONS for {subject} ({university}, {exam_type}).

Return ONLY valid JSON:
{{
  "five_mark_questions": [
    {{"question": "Q text", "marks": 5, "unit": "Unit 1", "difficulty": "Medium", "hint": "Optional"}}
  ],
  "ten_mark_questions": [
    {{"question": "Q text", "marks": 10, "unit": "Unit 1", "difficulty": "Hard", "hint": "Optional"}}
  ],
  "predicted_questions": [
    {{"question": "Q text", "marks": 10, "probability": "High", "reason": "Why important", "unit": "Unit 1"}}
  ]
}}

Generate: 8 five-mark, 6 ten-mark, 5 predicted questions."""
        
        # INCREASED: Need 1200 tokens for 8+6+5=19 questions
        response = await self._call_llm(prompt, max_tokens=1200, timeout=180)
        return self._safe_json_parse(response, {"five_mark_questions": [], "ten_mark_questions": [], "predicted_questions": []})
    
    async def _generate_mock_and_viva(self, subject: str, university: str, exam_type: str) -> Dict:
        """Generate mock test and viva questions"""
        logger.info("Generating mock test and viva...")
        
        prompt = f"""Generate MOCK TEST and VIVA for {subject} ({university}, {exam_type}).

Return ONLY valid JSON:
{{
  "mock_test": {{
    "section_a": {{
      "section_name": "Section A - MCQ",
      "instructions": "Choose correct answer",
      "questions": [{{"question": "Q1", "marks": 2}}],
      "total_marks": 20
    }},
    "section_b": {{
      "section_name": "Section B - Short",
      "instructions": "Answer in 100 words",
      "questions": [{{"question": "Q1", "marks": 5}}],
      "total_marks": 20
    }},
    "section_c": {{
      "section_name": "Section C - Long",
      "instructions": "Detailed answer",
      "questions": [{{"question": "Q1", "marks": 10}}],
      "total_marks": 10
    }}
  }},
  "viva_questions": [
    {{"question": "Viva Q", "expected_answer": "Answer", "unit": "Unit 1"}}
  ]
}}

Mock test: 50 marks total. Viva: 10 questions."""
        
        # INCREASED: Need 1200 tokens for full mock test (3 sections + viva)
        response = await self._call_llm(prompt, max_tokens=1200, timeout=180)
        return self._safe_json_parse(response, {"mock_test": {}, "viva_questions": []})
    
    async def _generate_ppt_and_plan(self, subject: str, university: str, exam_date: str | None) -> Dict:
        """Generate PPT content and study plan"""
        logger.info("Generating PPT and study plan...")
        
        date_info = f" Exam on {exam_date}." if exam_date else ""
        
        prompt = f"""Generate PPT SLIDES and STUDY PLAN for {subject} ({university}).{date_info}

Return ONLY valid JSON:
{{
  "ppt_content": [
    {{
      "slide_number": 1,
      "title": "Slide Title",
      "bullet_points": ["Point 1", "Point 2"],
      "diagram_suggestion": "Diagram idea"
    }}
  ],
  "study_plan": [
    {{
      "day_number": 1,
      "date": null,
      "tasks": ["Task 1", "Task 2"],
      "topics_to_cover": ["Topic 1"],
      "revision": false,
      "mock_test": false
    }}
  ]
}}

PPT: 8-10 slides. Study plan: 15 days."""
        
        # INCREASED: Need 300s timeout - 1800 tokens takes longer on CPU
        response = await self._call_llm(prompt, max_tokens=1800, timeout=300)
        return self._safe_json_parse(response, {"ppt_content": [], "study_plan": []})
    
    async def _call_llm(self, prompt: str, max_tokens: int = 600, timeout: int = 120) -> str:
        """Call LLM with focused prompt (OPTIMIZED with safety checks)"""
        
        # SAFETY: Truncate prompt if too large
        if len(prompt) > 5000:
            logger.warning(f"Prompt too large ({len(prompt)} chars), truncating to 5000")
            prompt = prompt[:5000] + "\n\n[Note: Truncated for performance]"
        
        # STRICT JSON-ONLY SYSTEM PROMPT
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an academic exam preparation assistant.\n\n"
                    "CRITICAL RULES:\n"
                    "- Return ONLY valid JSON\n"
                    "- Do NOT add explanations\n"
                    "- Do NOT wrap in markdown code blocks\n"
                    "- Do NOT add any text before or after JSON\n"
                    "- Output must be parseable by json.loads()\n"
                    "- Start with { and end with }"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = await llm_service.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            timeout=timeout  # Use provided timeout
        )
        
        return response
    
    def _safe_json_parse(self, text: str, fallback: Dict) -> Dict:
        """
        Safely parse JSON with multiple repair strategies
        
        Strategies:
        1. Direct parse
        2. Strip markdown code blocks
        3. Extract first {...} JSON block
        4. Fix trailing commas
        5. Log failure and return fallback
        """
        if not text or not text.strip():
            logger.warning("Empty LLM response, using fallback")
            return fallback
        
        # STRATEGY 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # STRATEGY 2: Strip markdown code blocks
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Remove ```json or ``` blocks
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
            
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
        
        # STRATEGY 3: Extract first JSON block using regex
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            extracted = json_match.group(0)
            try:
                return json.loads(extracted)
            except json.JSONDecodeError:
                # STRATEGY 4: Try fixing trailing commas
                fixed = re.sub(r',(\s*[}\]])', r'\1', extracted)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    pass
        
        # STRATEGY 5: All failed - log raw response
        logger.error(f"JSON parse failed after all strategies. Raw LLM output (first 500 chars):")
        logger.error(f"{text[:500]}")
        logger.warning(f"Using fallback: {fallback}")
        return fallback
    
    # ===== DATABASE PERSISTENCE METHODS =====
    
    async def save_preparation(
        self,
        user_id: str,
        subject: str,
        university: str,
        exam_type: str,
        exam_date: str | None,
        content: Dict,
        db: AsyncSession
    ) -> int:
        """Save preparation to database"""
        from app.models.preparation import Preparation
        
        logger.info(f"Saving preparation for user {user_id}: {subject}")
        
        # Clean content: remove fields that shouldn't be in JSON
        # (created_at is a separate column, preparation_id is internal)
        clean_content = {k: v for k, v in content.items() 
                        if k not in ['created_at', 'preparation_id']}
        
        prep = Preparation(
            user_id=user_id,
            subject=subject,
            university=university,
            exam_type=exam_type,
            exam_date=exam_date,
            content=clean_content
        )
        
        db.add(prep)
        await db.commit()
        await db.refresh(prep)
        
        logger.info(f"Preparation saved with ID: {prep.id}")
        return prep.id
    
    async def update_preparation_section(
        self,
        prep_id: int,
        section_data: Dict,
        db: AsyncSession
    ) -> None:
        """Update preparation with new section content (merge into existing JSON)"""
        from app.models.preparation import Preparation
        from sqlalchemy import select
        
        logger.info(f"Updating preparation {prep_id} with section keys: {list(section_data.keys())}")
        
        if not section_data:
            logger.warning(f"Empty section_data for prep {prep_id}, skipping update")
            return
        
        try:
            # Get current preparation
            query = select(Preparation).where(Preparation.id == prep_id)
            result = await db.execute(query)
            prep = result.scalar_one_or_none()
            
            if not prep:
                logger.error(f"Preparation {prep_id} not found")
                return
            
            # Merge new section data into existing content
            existing_content = dict(prep.content) if prep.content else {}
            updated_content = {**existing_content, **section_data}
            
            # Use ORM-style assignment for reliable JSON column updates
            prep.content = updated_content
            prep.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(prep)
            
            logger.info(f"Preparation {prep_id} updated successfully. Content keys: {list(updated_content.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to update preparation {prep_id}: {e}", exc_info=True)
            await db.rollback()
            raise


# Global instance
preparation_service = PreparationService()
