"""
Teacher Service
AI-powered roadmap generation and teaching logic
"""
import json
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.teacher import (
    TeacherRoadmap, TeacherModule, TeacherLessonState,
    TeacherCheckAttempt, TeacherMemoryCard,
    ModuleStatus, ModuleLevel, LessonPhase, CardType
)
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class TeacherService:
    """Service for AI teacher mode functionality"""
    
    async def generate_roadmap(
        self,
        subject: str,
        goal: Optional[str],
        user_id: str,
        db: AsyncSession
    ) -> TeacherRoadmap:
        """
        Generate AI-powered learning roadmap for a subject
        Returns 8-15 modules with structured objectives and topics
        """
        # Build prompt for AI to generate syllabus
        goal_context = f" for {goal}" if goal else ""
        
        prompt = f"""You are an expert teacher creating a structured learning roadmap for: {subject}{goal_context}

Generate a complete syllabus with 8-15 modules covering beginner to advanced topics.

For each module, provide:
1. Module title (clear and specific)
2. Level: beginner, intermediate, or advanced
3. Learning objectives (3-6 clear, measurable goals)
4. Lesson topics (3-8 specific subtopics to cover)
5. Prerequisites (which module indices must be completed first, if any)
6. Estimated time in minutes

Return ONLY a JSON array with this exact structure:
[
  {{
    "title": "Module title",
    "level": "beginner",
    "objectives": ["objective 1", "objective 2", ...],
    "topics": ["topic 1", "topic 2", ...],
    "prerequisites": [0, 1],
    "estimated_minutes": 30
  }}
]

Make it progressive: beginner → intermediate → advanced.
Ensure prerequisites form a valid learning path."""

        # Try to call LLM, but use fallback if it fails/times out
        try:
            response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse JSON response
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            modules_data = json.loads(content)
        except Exception as e:
            # LLM failed - use enhanced fallback
            logger.warning(f"LLM failed to generate roadmap: {e}. Using fallback.")
            modules_data = self._create_subject_specific_roadmap(subject, goal)
        
        # Create roadmap
        roadmap = TeacherRoadmap(
            user_id=user_id,
            subject=subject,
            goal=goal,
            total_modules=len(modules_data)
        )
        db.add(roadmap)
        await db.flush()
        
        # Create modules
        for index, module_data in enumerate(modules_data):
            # Determine level
            level_str = module_data.get("level", "beginner").lower()
            if "intermediate" in level_str:
                level = ModuleLevel.INTERMEDIATE
            elif "advanced" in level_str:
                level = ModuleLevel.ADVANCED
            else:
                level = ModuleLevel.BEGINNER
            
            # Determine initial status (first module unlocked)
            status = ModuleStatus.IN_PROGRESS if index == 0 else ModuleStatus.LOCKED
            
            module = TeacherModule(
                roadmap_id=roadmap.id,
                module_index=index,
                title=module_data["title"],
                level=level,
                objectives=module_data["objectives"],
                topics=module_data["topics"],
                prerequisites=module_data.get("prerequisites"),
                estimated_minutes=module_data.get("estimated_minutes", 30),
                status=status
            )
            db.add(module)
        
        # Flush to get module IDs
        await db.flush()
        
        # Now create lesson state for first module (after modules have IDs)
        if modules_data:
            first_module_result = await db.execute(
                select(TeacherModule)
                .where(
                    TeacherModule.roadmap_id == roadmap.id,
                    TeacherModule.module_index == 0
                )
            )
            first_module = first_module_result.scalar_one_or_none()
            if first_module:
                lesson_state = TeacherLessonState(module_id=first_module.id)
                db.add(lesson_state)
        
        await db.commit()
        await db.refresh(roadmap)
        
        return roadmap
    
    def _create_subject_specific_roadmap(self, subject: str, goal: Optional[str]) -> List[Dict]:
        """Enhanced fallback roadmap generator based on subject"""
        subject_lower = subject.lower()
        
        # Machine Learning roadmap
        if any(term in subject_lower for term in ['machine learning', 'ml', 'ai', 'artificial intelligence']):
            return [
                {
                    "title": "Introduction to Machine Learning",
                    "level": "beginner",
                    "objectives": ["Understand ML basics", "Learn types of ML", "Explore real-world applications"],
                    "topics": ["What is ML?", "Supervised vs Unsupervised", "Common algorithms overview"],
                    "prerequisites": None,
                    "estimated_minutes": 30
                },
                {
                    "title": "Python for Machine Learning",
                    "level": "beginner",
                    "objectives": ["Master NumPy and Pandas", "Data manipulation", "Visualization basics"],
                    "topics": ["NumPy arrays", "Pandas DataFrames", "Matplotlib basics"],
                    "prerequisites": [0],
                    "estimated_minutes": 45
                },
                {
                    "title": "Supervised Learning - Regression",
                    "level": "intermediate",
                    "objectives": ["Linear regression", "Polynomial regression", "Model evaluation"],
                    "topics": ["Linear models", "Loss functions", "R-squared and RMSE"],
                    "prerequisites": [1],
                    "estimated_minutes": 50
                },
                {
                    "title": "Supervised Learning - Classification",
                    "level": "intermediate",
                    "objectives": ["Logistic regression", "Decision trees", "Model selection"],
                    "topics": ["Classification algorithms", "Confusion matrix", "Accuracy metrics"],
                    "prerequisites": [2],
                    "estimated_minutes": 50
                },
                {
                    "title": "Neural Networks Fundamentals",
                    "level": "advanced",
                    "objectives": ["Understand perceptrons", "Backpropagation", "Activation functions"],
                    "topics": ["Neural network architecture", "Forward/backward pass", "Training process"],
                    "prerequisites": [3],
                    "estimated_minutes": 60
                }
            ]
        
        # Programming/coding roadmap
        elif any(term in subject_lower for term in ['programming', 'python', 'javascript', 'coding', 'web dev']):
            lang = "Python" if "python" in subject_lower else "Programming"
            return [
                {
                    "title": f"Introduction to {lang}",
                    "level": "beginner",
                    "objectives": ["Syntax basics", "Variables and data types", "Basic operations"],
                    "topics": ["Hello World", "Data types", "Operators"],
                    "prerequisites": None,
                    "estimated_minutes": 30
                },
                {
                    "title": "Control Flow",
                    "level": "beginner",
                    "objectives": ["If statements", "Loops", "Logic"],
                    "topics": ["Conditionals", "For/while loops", "Boolean logic"],
                    "prerequisites": [0],
                    "estimated_minutes": 40
                },
                {
                    "title": "Functions and Modules",
                    "level": "intermediate", 
                    "objectives": ["Define functions", "Parameters", "Code organization"],
                    "topics": ["Function syntax", "Return values", "Importing modules"],
                    "prerequisites": [1],
                    "estimated_minutes": 45
                },
                {
                    "title": "Data Structures",
                    "level": "intermediate",
                    "objectives": ["Lists and arrays", "Dictionaries", "Sets and tuples"],
                    "topics": ["List operations", "Dict methods", "Data structure choice"],
                    "prerequisites": [2],
                    "estimated_minutes": 50
                },
                {
                    "title": "Object-Oriented Programming",
                    "level": "advanced",
                    "objectives": ["Classes and objects", "Inheritance", "Polymorphism"],
                    "topics": ["Class design", "Methods", "OOP principles"],
                    "prerequisites": [3],
                    "estimated_minutes": 60
                }
            ]
        
        # Default generic roadmap for any subject
        else:
            return [
                {
                    "title": f"Introduction to {subject}",
                    "level": "beginner",
                    "objectives": ["Understand fundamental concepts", "Learn key terminology", "Explore overview"],
                    "topics": ["Basic definitions", "Historical context", "Why it matters"],
                    "prerequisites": None,
                    "estimated_minutes": 30
                },
                {
                    "title": f"Core Principles of {subject}",
                    "level": "beginner",
                    "objectives": ["Master foundational ideas", "Build mental models", "Practice basics"],
                    "topics": ["Key principles", "Common patterns", "Basic techniques"],
                    "prerequisites": [0],
                    "estimated_minutes": 45
                },
                {
                    "title": f"Intermediate {subject} Concepts",
                    "level": "intermediate",
                    "objectives": ["Apply knowledge", "Solve problems", "Build projects"],
                    "topics": ["Advanced techniques", "Problem-solving strategies", "Practical applications"],
                    "prerequisites": [1],
                    "estimated_minutes": 50
                },
                {
                    "title": f"Advanced {subject} Techniques",
                    "level": "advanced",
                    "objectives": ["Master complex topics", "Optimize solutions", "Best practices"],
                    "topics": ["Expert strategies", "Edge cases", "Performance"],
                    "prerequisites": [2],
                    "estimated_minutes": 60
                },
                {
                    "title": f"{subject} Mastery",
                    "level": "advanced",
                    "objectives": ["Synthesis", "Real-world application", "Continued learning"],
                    "topics": ["Integration", "Case studies", "Next steps"],
                    "prerequisites": [3],
                    "estimated_minutes": 60
                }
            ]
    
    def _create_fallback_roadmap(self, subject: str) -> List[Dict]:
        """Simple fallback - delegates to subject-specific"""
        return self._create_subject_specific_roadmap(subject, None)
    
    async def generate_teach_content(
        self,
        module_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate whiteboard-style teaching content for a module
        Uses RAG for accuracy where relevant
        """
        # Get module
        result = await db.execute(
            select(TeacherModule)
            .where(TeacherModule.id == module_id)
            .options(selectinload(TeacherModule.roadmap))
        )
        module = result.scalar_one()
        
        # Check if content already generated
        lesson_state_result = await db.execute(
            select(TeacherLessonState).where(TeacherLessonState.module_id == module_id)
        )
        lesson_state = lesson_state_result.scalar_one_or_none()
        
        if lesson_state and lesson_state.teach_content:
            return json.loads(lesson_state.teach_content)
        
        # Retrieve relevant context from RAG if available
        rag_context = ""
        try:
            context, _ = await rag_service.get_context_for_query(
                query=f"{module.title} {' '.join(module.topics[:3])}",
                subject_id=None,  # Search globally
                top_k=3
            )
            if context:
                rag_context = f"\n\nReference material:\n{context[:1000]}"
        except:
            pass
        
        # Build teaching prompt
        topics_str = "\n".join(f"- {topic}" for topic in module.topics)
        objectives_str = "\n".join(f"- {obj}" for obj in module.objectives)
        
        prompt = f"""You are a professional teacher teaching: {module.title}

Learning Objectives:
{objectives_str}

Topics to Cover:
{topics_str}
{rag_context}

Create structured CLASS-STYLE teaching content with these sections:

1. DEFINITIONS: Clear definitions of key terms
2. KEY CONCEPTS: Main ideas explained simply
3. EXAMPLES: 2-3 concrete examples
4. COMMON MISTAKES: What students often get wrong
5. SUMMARY: 3-4 bullet points recap

Use whiteboard/classroom tone: structured, friendly but professional.
Return as JSON with this structure:
{{
  "sections": [
    {{"type": "definition", "title": "Key Definitions", "content": "..."}},
    {{"type": "concept", "title": "Main Idea", "content": "..."}},
    {{"type": "example", "title": "Example 1", "content": "..."}},
    {{"type": "mistake", "title": "Common Mistakes", "content": "..."}},
    {{"type": "summary", "title": "Summary", "content": "..."}}
  ]
}}"""

        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1500
        )
        
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            teach_data = json.loads(content)
        except:
            # Fallback structure
            teach_data = {
                "sections": [
                    {"type": "definition", "title": "Introduction", "content": f"In this module, we'll learn about {module.title}."},
                    {"type": "summary", "title": "Key Points", "content": "\n".join(f"- {obj}" for obj in module.objectives)}
                ]
            }
        
        # Cache content
        if not lesson_state:
            lesson_state = TeacherLessonState(module_id=module_id)
            db.add(lesson_state)
        
        lesson_state.teach_content = json.dumps(teach_data)
        lesson_state.current_phase = LessonPhase.TEACH
        await db.commit()
        
        return teach_data
    
    async def generate_check_questions(
        self,
        module_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Generate 2-5 check questions to verify mastery
        Mix of MCQ and short answer
        """
        # Get module
        result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = result.scalar_one()
        
        objectives_str = "\n".join(f"- {obj}" for obj in module.objectives)
        topics_str = "\n".join(f"- {topic}" for topic in module.topics)
        
        prompt = f"""Create 4 check questions for: {module.title}

Learning Objectives:
{objectives_str}

Topics Covered:
{topics_str}

Generate:
- 2 MCQ questions (4 options each, one correct)
- 2 short answer questions

Return as JSON array:
[
  {{
    "question_id": "q1",
    "question_type": "mcq",
    "question_text": "Question here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A"
  }},
  {{
    "question_id": "q2",
    "question_type": "short_answer",
    "question_text": "Explain...",
    "correct_answer": "Expected answer outline"
  }}
]"""

        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1000
        )
        
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            questions = json.loads(content)
        except:
            # Fallback questions
            questions = [
                {
                    "question_id": "q1",
                    "question_type": "mcq",
                    "question_text": f"What is the main objective of {module.title}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": module.objectives[0] if module.objectives else "Option A"
                }
            ]
        
        return questions
    
    async def grade_check_answers(
        self,
        module_id: str,
        user_id: str,
        questions: List[Dict],
        answers: List[Dict],
        db: AsyncSession
    ) -> Tuple[float, bool, List[str], List[Dict]]:
        """
        Grade student answers
        Returns: (score, passed, weak_topics, grading_details)
        """
        grading_details = []
        correct_count = 0
        weak_topics = []
        
        answer_map = {ans["question_id"]: ans["answer"] for ans in answers}
        
        for question in questions:
            qid = question["question_id"]
            student_answer = answer_map.get(qid, "")
            
            if question["question_type"] == "mcq":
                # Exact match for MCQ
                correct = student_answer.strip() == question["correct_answer"].strip()
                grading_details.append({
                    "question_id": qid,
                    "correct": correct,
                    "feedback": "Correct!" if correct else f"Correct answer: {question['correct_answer']}"
                })
                if correct:
                    correct_count += 1
            else:
                # Use LLM to grade short answer
                grade_prompt = f"""Grade this answer:

Question: {question['question_text']}
Student Answer: {student_answer}
Expected Answer: {question['correct_answer']}

Is the student's answer correct? Reply with ONLY 'YES' or 'NO' and a brief feedback."""

                grade_response = await llm_service.chat_completion(
                    messages=[{"role": "user", "content": grade_prompt}],
                    temperature=0.2,
                    max_tokens=100
                )
                
                correct = "yes" in grade_response.lower()[:10]
                grading_details.append({
                    "question_id": qid,
                    "correct": correct,
                    "feedback": grade_response.strip()
                })
                if correct:
                    correct_count += 1
                else:
                    # Add topic as weak if failed
                    if len(weak_topics) < 3:
                        weak_topics.append(question["question_text"][:50])
        
        # Calculate score
        score = correct_count / len(questions) if questions else 0
        passed = score >= 0.7  # 70% threshold
        
        # Save attempt
        attempt = TeacherCheckAttempt(
            module_id=module_id,
            user_id=user_id,
            questions=questions,
            answers=answers,
            score=score,
            passed=1 if passed else 0,
            weak_topics=weak_topics if weak_topics else None,
            grading_details=grading_details
        )
        db.add(attempt)
        
        # Update lesson state
        lesson_state_result = await db.execute(
            select(TeacherLessonState).where(TeacherLessonState.module_id == module_id)
        )
        lesson_state = lesson_state_result.scalar_one_or_none()
        if lesson_state:
            lesson_state.check_attempts += 1
            
            if passed:
                lesson_state.current_phase = LessonPhase.TEACH  # Reset for next module
            else:
                lesson_state.current_phase = LessonPhase.RETEACH
        
        # Update module status
        module_result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = module_result.scalar_one()
        module.mastery_score = score
        
        if passed:
            module.status = ModuleStatus.MASTERED
            
            # Unlock next module
            await self._unlock_next_module(module, db)
        
        await db.commit()
        
        return score, passed, weak_topics, grading_details
    
    async def _unlock_next_module(self, current_module: TeacherModule, db: AsyncSession):
        """Unlock the next sequential module"""
        next_result = await db.execute(
            select(TeacherModule)
            .where(
                TeacherModule.roadmap_id == current_module.roadmap_id,
                TeacherModule.module_index == current_module.module_index + 1
            )
        )
        next_module = next_result.scalar_one_or_none()
        
        if next_module and next_module.status == ModuleStatus.LOCKED:
            next_module.status = ModuleStatus.IN_PROGRESS
            
            # Create lesson state for next module
            lesson_state = TeacherLessonState(module_id=next_module.id)
            db.add(lesson_state)
        
        # Update roadmap progress
        roadmap_result = await db.execute(
            select(TeacherRoadmap).where(TeacherRoadmap.id == current_module.roadmap_id)
        )
        roadmap = roadmap_result.scalar_one()
        
        completed_count = await db.scalar(
            select(TeacherModule)
            .where(
                TeacherModule.roadmap_id == roadmap.id,
                TeacherModule.status == ModuleStatus.MASTERED
            )
        )
        
        roadmap.completed_modules = completed_count
        roadmap.overall_progress = completed_count / roadmap.total_modules if roadmap.total_modules > 0 else 0
    
    async def generate_reteach_content(
        self,
        module_id: str,
        weak_topics: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate simplified reteach content for weak topics
        Includes practice questions
        """
        module_result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = module_result.scalar_one()
        
        weak_topics_str = "\n".join(f"- {topic}" for topic in weak_topics)
        
        prompt = f"""The student struggled with these topics in {module.title}:

{weak_topics_str}

Provide:
1. SIMPLIFIED explanations for each weak topic (use simpler language, more examples)
2. 2 practice questions to help reinforce learning

Return as JSON:
{{
  "explanations": [
    {{"topic": "topic name", "explanation": "simpler explanation with examples"}}
  ],
  "practice_questions": [
    {{"question_type": "mcq", "question_text": "...", "options": [...], "correct_answer": "..."}}
  ]
}}"""

        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800
        )
        
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            reteach_data = json.loads(content)
        except:
            reteach_data = {
                "explanations": [{"topic": topic, "explanation": f"Let's review {topic} again with simpler examples."} for topic in weak_topics],
                "practice_questions": []
            }
        
        # Cache reteach content
        lesson_state_result = await db.execute(
            select(TeacherLessonState).where(TeacherLessonState.module_id == module_id)
        )
        lesson_state = lesson_state_result.scalar_one_or_none()
        if lesson_state:
            lesson_state.reteach_content = json.dumps(reteach_data)
            await db.commit()
        
        return reteach_data
    
    async def generate_memory_cards(
        self,
        module_id: str,
        db: AsyncSession
    ) -> List[TeacherMemoryCard]:
        """
        Generate 3-7 memory cards after module mastery
        Key formulas, concepts, mistakes, examples
        """
        # Check if cards already exist
        existing_cards_result = await db.execute(
            select(TeacherMemoryCard)
            .where(TeacherMemoryCard.module_id == module_id)
            .order_by(TeacherMemoryCard.display_order)
        )
        existing_cards = existing_cards_result.scalars().all()
        if existing_cards:
            return list(existing_cards)
        
        # Get module
        module_result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = module_result.scalar_one()
        
        topics_str = "\n".join(f"- {topic}" for topic in module.topics)
        
        prompt = f"""Create 5 memory/flashcards for: {module.title}

Topics covered:
{topics_str}

Create cards for:
- 2 key concepts/formulas
- 1 common mistake to avoid  
- 2 micro-examples

Return as JSON array:
[
  {{
    "card_type": "concept",
    "front_text": "What is...?",
    "back_text": "Definition/explanation"
  }},
  {{
    "card_type": "mistake",
    "front_text": "Common mistake:",
    "back_text": "Explanation of mistake"
  }}
]

Card types: concept, formula, mistake, example"""

        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=800
        )
        
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            cards_data = json.loads(content)
        except:
            # Fallback cards
            cards_data = [
                {
                    "card_type": "concept",
                    "front_text": f"What did we learn in {module.title}?",
                    "back_text": module.objectives[0] if module.objectives else "Key concepts"
                }
            ]
        
        # Create cards in DB
        cards = []
        for i, card_data in enumerate(cards_data):
            card_type_str = card_data.get("card_type", "concept")
            if "formula" in card_type_str:
                card_type = CardType.FORMULA
            elif "mistake" in card_type_str:
                card_type = CardType.MISTAKE
            elif "example" in card_type_str:
                card_type = CardType.EXAMPLE
            else:
                card_type = CardType.CONCEPT
            
            card = TeacherMemoryCard(
                module_id=module_id,
                card_type=card_type,
                front_text=card_data["front_text"],
                back_text=card_data["back_text"],
                display_order=i
            )
            db.add(card)
            cards.append(card)
        
        await db.commit()
        
        return cards


teacher_service = TeacherService()
