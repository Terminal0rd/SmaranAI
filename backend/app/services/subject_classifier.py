"""
Subject Classifier Service
Automatically detects subject/topic from PDF content using LLM
"""
import logging
from typing import List, Optional
from app.services.llm_service import llm_service
from app.models.subject import Subject

logger = logging.getLogger(__name__)


class SubjectClassifier:
    """Automatically classify documents and queries into subjects"""
    
    def __init__(self):
        self.confidence_threshold = 0.7  # 70% confidence minimum
    
    async def classify_document(
        self,
        text_sample: str,
        available_subjects: List[Subject]
    ) -> tuple[str, float]:
        """
        Classify a document into one of the available subjects
        
        Args:
            text_sample: First ~1000 chars from document
            available_subjects: List of Subject models
            
        Returns:
            Tuple of (subject_id, confidence_score)
        """
        if not available_subjects:
            logger.warning("[Classifier] No subjects available")
            return None, 0.0
        
        # Build subject list for LLM
        subject_list = "\n".join([
            f"- {s.name}: {s.description or 'No description'}"
            for s in available_subjects
        ])
        
        prompt = f"""You are a document classifier. Analyze this text sample and determine which subject it belongs to.

Available Subjects:
{subject_list}

Document Sample:
{text_sample[:1000]}

RULES:
1. Return ONLY the exact subject name, nothing else
2. If the content clearly matches a subject, return that subject name
3. If unsure or content is mixed/generic, return "General"
4. Do NOT make up subjects - only choose from the list above

Subject:"""

        try:
            response = await llm_service.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.3  # Low temp for consistent classification
            )
            
            predicted_subject_name = response.strip().strip('"\'')
            
            # Find matching subject
            for subject in available_subjects:
                if subject.name.lower() == predicted_subject_name.lower():
                    confidence = 0.85  # High confidence for exact match
                    logger.info(f"[Classifier] Document classified as '{subject.name}' (confidence: {confidence:.2f})")
                    return subject.id, confidence
            
            # If "General" was returned or no match found
            general_subject = next(
                (s for s in available_subjects if s.name.lower() == "general"),
                None
            )
            
            if general_subject:
                confidence = 0.5  # Lower confidence for fallback
                logger.info(f"[Classifier] Falling back to 'General' (confidence: {confidence:.2f})")
                return general_subject.id, confidence
            
            # Ultimate fallback: first subject
            logger.warning(f"[Classifier] No 'General' subject found, using first available: {available_subjects[0].name}")
            return available_subjects[0].id, 0.3
            
        except Exception as e:
            logger.error(f"[Classifier] Classification failed: {e}")
            # Return first subject as safe fallback
            return available_subjects[0].id if available_subjects else None, 0.0
    
    async def classify_query(
        self,
        query: str,
        available_subjects: List[Subject]
    ) -> Optional[str]:
        """
        Classify a user query into a subject for better search routing
        
        Args:
            query: User's question
            available_subjects: List of Subject models
            
        Returns:
            subject_id or None if confidence too low
        """
        if not available_subjects or len(query) < 10:
            return None
        
        subject_list = "\n".join([f"- {s.name}" for s in available_subjects])
        
        prompt = f"""Classify this question into ONE subject category.

Available Subjects:
{subject_list}

Question: {query}

Return ONLY the subject name or "unclear" if the question doesn't fit any category.

Subject:"""
        
        try:
            response = await llm_service.generate(
                prompt=prompt,
                max_tokens=30,
                temperature=0.2
            )
            
            predicted_name = response.strip().strip('"\'').lower()
            
            # Find matching subject
            for subject in available_subjects:
                if subject.name.lower() == predicted_name:
                    logger.info(f"[Classifier] Query classified as '{subject.name}'")
                    return subject.id
            
            logger.info("[Classifier] Query classification unclear - using global search")
            return None
            
        except Exception as e:
            logger.error(f"[Classifier] Query classification failed: {e}")
            return None


# Global instance
subject_classifier = SubjectClassifier()
