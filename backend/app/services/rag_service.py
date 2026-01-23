"""
RAG (Retrieval-Augmented Generation) service
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.session import Session, Message
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-powered responses"""
    
    async def get_context_for_query(
        self,
        query: str,
        subject_id: Optional[str] = None,
        top_k: int = 5
    ) -> Tuple[str, List[dict]]:
        """
        Retrieve relevant context for a query
        SMART SEARCH: Prioritizes current subject, falls back to all subjects
        
        Args:
            query: User's question
            subject_id: Optional subject filter (prioritized)
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (context string, sources list)
        """
        # First: Search within the current subject
        results = embedding_service.search(query, top_k=top_k, subject_id=subject_id)
        
        # If not enough quality results, search globally
        quality_results = [r for r in results if r['score'] > 0.3]
        
        if len(quality_results) < 3 and subject_id:
            logger.info(f"Only {len(quality_results)} results in subject {subject_id}, searching globally...")
            global_results = embedding_service.search(query, top_k=top_k, subject_id=None)
            
            # Merge results, prioritizing subject-specific ones
            all_results = results + [r for r in global_results if r not in results]
            results = all_results[:top_k]
        
        if not results:
            return "", []
        
        # Build context from top results
        context_parts = []
        sources = []
        
        for result in results:
            if result['score'] > 0.3:  # Only include relevant results
                metadata = result['metadata']
                context_parts.append(metadata['content'])
                
                # Mark if from current subject or cross-subject
                source_info = {
                    'filename': metadata['filename'],
                    'chunk_preview': metadata.get('content_preview', metadata['content'][:100])
                }
                
                # Add indicator if from different subject
                if subject_id and metadata.get('subject_id') != subject_id:
                    source_info['cross_subject'] = True
                    
                sources.append(source_info)
        
        context = "\n\n---\n\n".join(context_parts)
        return context, sources
    
    async def get_session_summary(
        self,
        db: AsyncSession,
        session_id: str
    ) -> str:
        """
        Get a summary of the session conversation
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            Session summary
        """
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()
        
        if not messages or len(messages) < 3:
            return ""
        
        # Format messages for summarization
        message_list = [
            {"role": m.role, "content": m.content}
            for m in messages[-10:]  # Last 10 messages
        ]
        
        try:
            summary = await llm_service.summarize_session(message_list)
            return summary
        except Exception:
            return ""
    
    async def generate_response(
        self,
        db: AsyncSession,
        session_id: str,
        subject_id: str,
        question: str
    ) -> Tuple[str, str, List[dict], List[str]]:
        """
        Generate a RAG-powered response
        
        Args:
            db: Database session
            session_id: Session ID
            subject_id: Subject ID
            question: User's question
            
        Returns:
            Tuple of (response, formatted_response, sources, concepts)
        """
        # Get RAG context
        context, sources = await self.get_context_for_query(
            question, 
            subject_id=subject_id,
            top_k=5
        )
        
        # Get session summary
        session_summary = await self.get_session_summary(db, session_id)
        
        # Generate response
        response = await llm_service.generate_whiteboard_response(
            question=question,
            context=context,
            session_summary=session_summary
        )
        
        # Extract concepts (with improved fallback)
        concepts = []
        try:
            concepts = await llm_service.extract_concepts(response)
            logger.info(f"LLM extracted {len(concepts)} concepts: {concepts}")
        except Exception as e:
            logger.warning(f"LLM concept extraction failed: {e}, using fallback")
            # Fallback: extract keywords from question and response
            import re
            
            # Combine question and response
            text = question + " " + response[:1000]
            
            # Extract multi-word capitalized phrases (e.g., "Machine Learning", "Neural Networks")
            multi_word = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
            
            # Extract single capitalized words (but filter common words)
            single_word = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
            
            # Common words to exclude
            exclude = {'The', 'This', 'That', 'These', 'Those', 'What', 'When', 'Where', 'Why', 'How', 
                      'Which', 'Who', 'Explain', 'Define', 'Describe', 'Tell', 'Give', 'Show', 'True', 'False'}
            
            # Combine and filter
            all_concepts = multi_word + [w for w in single_word if w not in exclude]
            
            # Get unique concepts, limit to 8
            concepts = list(dict.fromkeys(all_concepts))[:8]
            
            logger.info(f"Fallback extracted {len(concepts)} concepts: {concepts}")
            
            # If still no concepts, create one from the question
            if not concepts and question:
                # Extract nouns from question as a last resort
                words = question.split()
                concepts = [w.capitalize() for w in words if len(w) > 4 and w.lower() not in 
                          {'what', 'explain', 'describe', 'about', 'tell', 'give', 'show'}][:3]
                logger.info(f"Last resort extracted {len(concepts)} concepts from question: {concepts}")
        
        return response, response, sources, concepts
    
    async def get_youtube_recommendations(
        self,
        topic: str,
        subject_name: str,
        num_results: int = 5
    ) -> List[dict]:
        """
        Get YouTube video recommendations
        
        Args:
            topic: Topic to find videos for
            subject_name: Subject area
            num_results: Number of recommendations
            
        Returns:
            List of YouTube search suggestions
        """
        try:
            keywords = await llm_service.generate_youtube_keywords(topic, subject_name)
        except Exception:
            # Fallback to simple keywords
            keywords = [f"{subject_name} {topic} tutorial"]
        
        recommendations = []
        for i, query in enumerate(keywords[:num_results]):
            encoded_query = query.replace(' ', '+')
            recommendations.append({
                'title': query,
                'search_query': query,
                'search_url': f"https://www.youtube.com/results?search_query={encoded_query}"
            })
        
        return recommendations


# Global instance
rag_service = RAGService()
