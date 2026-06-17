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
        Generate quiz STRICTLY from session content
        **FIXED**: No placeholder questions, grounds in actual session learning
        
        Args:
            db: Database session
            user_id: User ID
            session_id: Session ID
            subject_id: Subject ID
            num_questions: Number of questions (5-10)
            question_types: Types of questions
            
        Returns:
            Tuple of (QuizAttempt, list of QuizQuestions)
            
        Raises:
            ValueError: If session has insufficient learning content
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if question_types is None:
            question_types = ["mcq", "true_false"]
        
        # STEP 1: Get session messages (AI responses = learning content)
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id, Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .limit(10)  # Get up to 10 most recent AI responses
        )
        messages = result.scalars().all()
        
        if len(messages) < 2:
            raise ValueError(
                "Not enough learning content to generate quiz. "
                "Please have at least 3-4 conversation exchanges first."
            )
        
        # STEP 2: Extract and preprocess content from messages
        content_parts = []
        for msg in messages[:3]:  # Use top 3 most recent for speed
            # Take first 600 chars from each message
            content_parts.append(msg.content[:600])
        
        # STEP 3: Get RAG chunks that were used in session (top 3)
        search_query = " ".join([m.content[:200] for m in messages[:2]])
        
        try:
            rag_results = embedding_service.search(
                query=search_query,
                top_k=3,
                subject_id=subject_id
            )
            
            for result in rag_results:
                if result['score'] > 0.3:
                    content_parts.append(result['metadata'].get('content', '')[:500])
        except Exception as e:
            logger.warning(f"RAG search failed during quiz gen: {e}")
        
        # STEP 4: Combine and preprocess content (strip markdown, limit size)
        raw_content = "\n\n".join(content_parts)
        full_content = self._preprocess_session_content(raw_content, max_chars=1200)
        
        if len(full_content) < 200:
            raise ValueError(
                "Session content too short to generate meaningful quiz questions."
            )
        
        logger.info(f"[Quiz Gen] Generating {num_questions} questions from {len(full_content)} chars")
        
        # STEP 5: Generate questions with RETRY LOGIC (max 2 retries)
        questions_data = []
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[Quiz Gen] Attempt {attempt + 1}/{max_retries}")
                
                questions_json = await llm_service.generate_quiz_questions(
                    full_content,
                    num_questions,
                    question_types
                )
                
                # Strict validation with new schema
                questions_data = self._validate_quiz_json(questions_json, num_questions)
                
                if questions_data:
                    logger.info(f"[Quiz Gen] Successfully validated {len(questions_data)} questions")
                    break
                    
            except (ValueError, json.JSONDecodeError) as e:
                last_error = str(e)
                logger.warning(f"[Quiz Gen] Attempt {attempt + 1} failed: {e}")
                
                if attempt == max_retries - 1:
                    logger.error(f"[Quiz Gen] All retry attempts failed")
                    raise ValueError(
                        "Quiz generation failed. The content may be too short or "
                        "the AI couldn't generate valid questions. Please try again."
                    )
                continue
        
        if not questions_data:
            raise ValueError("Failed to generate valid quiz questions")
        
        # Create quiz attempt
        attempt = QuizAttempt(
            user_id=user_id,
            session_id=session_id,
            subject_id=subject_id,
            total_questions=len(questions_data)
        )
        db.add(attempt)
        await db.flush()
        
        # Create question records with randomized options
        questions = []
        for q_data in questions_data:
            # Randomize option order to prevent correct answer always being first
            randomized = self._randomize_options(q_data)
            
            # Convert correct_index to answer letter for storage
            correct_letter = chr(65 + randomized['correct_index'])  # 0->A, 1->B, etc.
            
            question = QuizQuestion(
                attempt_id=attempt.id,
                question_type='mcq',
                question_text=randomized['question'],
                options=randomized['options'],
                correct_answer=correct_letter,
                source_concept=randomized.get('explanation', 'Session Learning')[:100]
            )
            db.add(question)
            questions.append(question)
        
        await db.commit()
        await db.refresh(attempt)
        
        
        logger.info(f"[Quiz Gen] Created quiz with {len(questions)} questions")
        return attempt, questions
    
    def _is_placeholder_question(self, question_data: dict) -> bool:
        """Check if question is a placeholder/template"""
        question_text = question_data.get('question', '').lower()
        
        # Reject placeholder patterns
        placeholder_patterns = [
            'sample question',
            'placeholder',
            'example question',
            'test question',
            'option 1',
            'option 2',
            '...',
            'fill in'
        ]
        
        return any(pattern in question_text for pattern in placeholder_patterns)
    
    def _create_content_based_questions(
        self,
        content: str,
        num_questions: int,
        messages: list
    ) -> List[dict]:
        """Create real questions directly from session content with REALISTIC distractors"""
        import re
        
        questions = []
        
        # Extract sentences and key concepts from content
        sentences = [
            s.strip() 
            for s in re.split(r'[.!?]+', content)
            if len(s.strip()) > 40
        ]
        
        if not sentences:
            return []
        
        # Extract key terms/concepts for creating realistic distractors
        # Look for capitalized words, technical terms, numbers
        terms = []
        for sentence in sentences[:20]:  # Scan first 20 sentences
            # Extract capitalized terms (likely concepts)
            words = sentence.split()
            for word in words:
                if len(word) > 3 and (word[0].isupper() or word.isdigit()):
                    terms.append(word.strip('.,;:()[]'))
        
        # Create questions from actual content
        for i in range(min(num_questions, len(sentences))):
            correct_sentence = sentences[i]
            
            if i % 2 == 0 and len(sentences) > 3:  # MCQ with realistic distractors
                # Get related sentences for distractor options
                distractor_sentences = [s for j, s in enumerate(sentences) if j != i and len(s) > 30][:3]
                
                options = [f'A) {correct_sentence[:75]}']
                
                # Generate realistic distractors from other content
                for idx, dist in enumerate(distractor_sentences[:3]):
                    letter = chr(66 + idx)  # B, C, D
                    # Modify slightly to make it wrong but plausible
                    distractor = dist[:75]
                    options.append(f'{letter}) {distractor}')
                
                # Fill remaining options if needed
                while len(options) < 4:
                    letter = chr(65 + len(options))
                    if len(terms) > len(options):
                        # Create distractor using different terms
                        alt_term = terms[len(options) % len(terms)]
                        options.append(f'{letter}) Related to {alt_term} but not the main concept')
                    else:
                        options.append(f'{letter}) A different aspect of the topic discussed')
                
                questions.append({
                    'type': 'mcq',
                    'question': f"According to the lesson, which of the following is accurate?",
                    'options': options[:4],
                    'answer': 'A',
                    'concept': 'Session Content'
                })
            else:  # True/False based on content
                questions.append({
                    'type': 'true_false',
                    'question': f"True or False: {correct_sentence[:100]}",
                    'answer': 'True',
                    'concept': 'Session Content'
                })
        
        return questions
    
    
    def _preprocess_session_content(self, content: str, max_chars: int = 1200) -> str:
        """Strip markdown tokens and limit content for quiz generation"""
        import re
        
        # Remove code blocks
        content = re.sub(r'```[\s\S]*?```', '', content)
        
        # Remove markdown formatting
        content = re.sub(r'#{1,6}\s', '', content)  # Headers
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)  # Italic
        content = re.sub(r'`(.+?)`', r'\1', content)  # Inline code
        content = re.sub(r'---+', '', content)  # Horizontal rules
        
        # Clean whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        # Limit length
        if len(content) > max_chars:
            content = content[:max_chars]
        
        return content
    
    def _validate_quiz_json(self, raw_json: str, expected_count: int) -> List[dict]:
        """Parse and validate quiz JSON with STRICT checks and ROBUST parsing"""
        import re
        
        # ROBUST JSON PARSING: Multiple strategies
        parsed_data = None
        
        # STRATEGY 1: Direct parse
        try:
            parsed_data = json.loads(raw_json)
        except json.JSONDecodeError:
            pass
        
        # STRATEGY 2: Strip markdown code blocks
        if not parsed_data:
            cleaned = raw_json.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
                
                try:
                    parsed_data = json.loads(cleaned)
                except json.JSONDecodeError:
                    pass
        
        # STRATEGY 3: Extract first JSON block using regex
        if not parsed_data:
            json_match = re.search(r'\{.*\}', raw_json, re.DOTALL)
            if json_match:
                extracted = json_match.group(0)
                try:
                    parsed_data = json.loads(extracted)
                except json.JSONDecodeError:
                    # STRATEGY 4: Fix trailing commas and retry
                    fixed = re.sub(r',(\s*[}\]])', r'\1', extracted)
                    try:
                        parsed_data = json.loads(fixed)
                    except json.JSONDecodeError:
                        pass
        
        # STRATEGY 5: Progressive truncation repair (BULLETPROOF)
        # The LLM generates valid JSON that gets truncated. We find the last
        # point where the JSON is valid by scanning backwards through closing braces.
        if not parsed_data:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info("[Quiz JSON Repair] Attempting progressive truncation repair...")
            
            # Find all positions of closing braces (potential question boundaries)
            brace_positions = [i for i, c in enumerate(raw_json) if c == '}']
            
            # Try from the LAST closing brace backwards
            for pos in reversed(brace_positions):
                candidate = raw_json[:pos + 1].rstrip().rstrip(',')
                
                # Try closing as {"questions": [...]}
                for closing in ['\n  ]\n}', ']}', '\n]\n}']:
                    try:
                        test = candidate + closing
                        result = json.loads(test)
                        if isinstance(result, dict) and "questions" in result and len(result["questions"]) >= 1:
                            parsed_data = result
                            _logger.info(
                                f"[Quiz JSON Repair] SUCCESS - Recovered {len(result['questions'])} "
                                f"questions by truncating at position {pos}"
                            )
                            break
                    except (json.JSONDecodeError, Exception):
                        continue
                
                if parsed_data:
                    break
            
            # STRATEGY 6: Parse each question object individually
            if not parsed_data:
                _logger.info("[Quiz JSON Repair] Trying individual question extraction...")
                individual_questions = []
                
                # Find all { that start a question object
                q_starts = [m.start() for m in re.finditer(r'\{\s*"question"', raw_json)]
                
                for i, start in enumerate(q_starts):
                    # Find the matching closing brace for this question
                    # Try each } after this start position
                    for end_pos in range(start + 1, len(raw_json)):
                        if raw_json[end_pos] == '}':
                            candidate = raw_json[start:end_pos + 1]
                            try:
                                q_obj = json.loads(candidate)
                                if "question" in q_obj and "options" in q_obj:
                                    individual_questions.append(q_obj)
                                    break  # Found valid end for this question
                            except json.JSONDecodeError:
                                continue
                
                if individual_questions:
                    parsed_data = {"questions": individual_questions}
                    _logger.info(
                        f"[Quiz JSON Repair] SUCCESS - Extracted {len(individual_questions)} "
                        f"individual questions"
                    )
        
        # If all strategies failed
        if not parsed_data:
            raise ValueError(f"Invalid JSON syntax: Could not parse response after all repair attempts. First 200 chars: {raw_json[:200]}")
        
        data = parsed_data
        
        # Handle case where LLM returns a bare JSON array instead of {"questions": [...]}
        if isinstance(data, list):
            data = {"questions": data}
        
        # Validate structure
        if "questions" not in data or not isinstance(data["questions"], list):
            raise ValueError("JSON missing 'questions' array")
        
        questions = data["questions"]
        if not questions:
            raise ValueError("Questions array is empty")
        
        validated = []
        
        # Forbidden phrases in options
        forbidden_phrases = [
            "not discussed", "opposite", "none of the above",
            "all of the above", "placeholder", "option 1",
            "option 2", "option 3", "option 4", "..."
        ]
        
        # Pattern to detect markdown tokens
        markdown_pattern = re.compile(r'[*#`]{2,}|```|\*\*|__')
        
        for idx, q in enumerate(questions):
            # Check required fields
            if "question" not in q:
                continue
            if "options" not in q:
                continue
            if "correct_index" not in q:
                continue
            
            # Validate question text
            question_text = q["question"].strip()
            if not question_text or len(question_text) < 10:
                continue
            
            # Check for markdown in question
            if markdown_pattern.search(question_text):
                continue
            
            # Validate options
            options = q["options"]
            if not isinstance(options, list):
                continue
            if len(options) != 4:
                continue
            
            # Clean and validate each option
            cleaned_options = []
            valid = True
            
            for opt in options:
                if not isinstance(opt, str):
                    valid = False
                    break
                
                opt_clean = opt.strip()
                
                # Check length
                if len(opt_clean) < 5 or len(opt_clean) > 200:
                    valid = False
                    break
                
                # Check for markdown tokens
                if markdown_pattern.search(opt_clean):
                    valid = False
                    break
                
                # Check for letter prefixes (A), B), etc.) - should be plain text
                if re.match(r'^[A-Da-d]\)', opt_clean):
                    valid = False
                    break
                
                cleaned_options.append(opt_clean)
            
            if not valid:
                continue
            
            # Check for duplicate options
            if len(set(cleaned_options)) != 4:
                continue
            
            # Check for forbidden phrases
            combined_text = " ".join(cleaned_options).lower()
            if any(phrase in combined_text for phrase in forbidden_phrases):
                continue
            
            # Validate correct_index
            correct_idx = q["correct_index"]
            if not isinstance(correct_idx, int):
                continue
            if not (0 <= correct_idx <= 3):
                continue
            
            # Add validated question
            validated.append({
                "question": question_text,
                "options": cleaned_options,
                "correct_index": correct_idx,
                "explanation": q.get("explanation", "")
            })
        
        # Ensure we have at least 1 valid question (better short quiz than no quiz)
        if len(validated) < 1:
            raise ValueError(
                f"No valid questions generated ({expected_count} expected). "
                f"Questions may contain markdown, duplicates, or forbidden phrases."
            )
        
        return validated[:expected_count]
    
    def _randomize_options(self, question: dict) -> dict:
        """Shuffle options and update correct_index to prevent answer always being first"""
        import random
        
        options = question["options"].copy()
        correct_idx = question["correct_index"]
        correct_answer = options[correct_idx]
        
        # Shuffle options
        random.shuffle(options)
        
        # Find new position of correct answer
        new_correct_idx = options.index(correct_answer)
        
        return {
            **question,
            "options": options,
            "correct_index": new_correct_idx
        }
    
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
