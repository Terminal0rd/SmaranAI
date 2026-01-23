"""
RAG (Retrieval-Augmented Generation) service
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session, Message
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service


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
        
        Args:
            query: User's question
            subject_id: Optional subject filter
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (context string, sources list)
        """
        results = embedding_service.search(query, top_k=top_k, subject_id=subject_id)
        
        if not results:
            return "", []
        
        # Build context from top results
        context_parts = []
        sources = []
        
        for result in results:
            if result['score'] > 0.3:  # Only include relevant results
                metadata = result['metadata']
                context_parts.append(metadata['content'])
                sources.append({
                    'filename': metadata['filename'],
                    'chunk_preview': metadata.get('content_preview', metadata['content'][:100])
                })
        
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
        
        # Extract concepts
        try:
            concepts = await llm_service.extract_concepts(response)
        except Exception:
            concepts = []
        
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
