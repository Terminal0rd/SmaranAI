"""
MindMap service for concept tracking
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import math

from app.models.mindmap import MindMapNode, MindMapEdge
from app.services.llm_service import llm_service


class MindMapService:
    """Service for managing concept mind maps"""
    
    async def get_mindmap(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str
    ) -> Tuple[List[MindMapNode], List[MindMapEdge]]:
        """
        Get all nodes and edges for a subject
        
        Args:
            db: Database session
            user_id: User ID
            subject_id: Subject ID
            
        Returns:
            Tuple of (nodes, edges)
        """
        # Get nodes
        result = await db.execute(
            select(MindMapNode)
            .where(
                MindMapNode.user_id == user_id,
                MindMapNode.subject_id == subject_id
            )
        )
        nodes = list(result.scalars().all())
        
        if not nodes:
            return [], []
        
        # Get edges
        node_ids = [n.id for n in nodes]
        result = await db.execute(
            select(MindMapEdge)
            .where(MindMapEdge.source_node_id.in_(node_ids))
        )
        edges = list(result.scalars().all())
        
        return nodes, edges
    
    async def add_concepts(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str,
        concepts: List[str]
    ) -> List[MindMapNode]:
        """
        Add new concepts to the mind map
        
        Args:
            db: Database session
            user_id: User ID
            subject_id: Subject ID
            concepts: List of concept names
            
        Returns:
            List of created nodes
        """
        if not concepts:
            return []
        
        # Get existing nodes
        result = await db.execute(
            select(MindMapNode)
            .where(
                MindMapNode.user_id == user_id,
                MindMapNode.subject_id == subject_id
            )
        )
        existing_nodes = {n.label.lower(): n for n in result.scalars().all()}
        
        # Calculate positions for new nodes
        num_existing = len(existing_nodes)
        
        new_nodes = []
        for i, concept in enumerate(concepts):
            if concept.lower() in existing_nodes:
                continue
            
            # Calculate position in a spiral layout
            angle = (num_existing + i) * 0.5
            radius = 100 + ((num_existing + i) // 8) * 80
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            node = MindMapNode(
                subject_id=subject_id,
                user_id=user_id,
                label=concept,
                x_position=x,
                y_position=y,
                mastery_level=0.0,
                status="learning"
            )
            db.add(node)
            new_nodes.append(node)
        
        if new_nodes:
            await db.flush()
            
            # Try to create edges between related concepts
            await self._create_edges(db, user_id, subject_id, new_nodes)
            
            await db.commit()
            for node in new_nodes:
                await db.refresh(node)
        
        return new_nodes
    
    async def _create_edges(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str,
        new_nodes: List[MindMapNode]
    ):
        """Create edges between related nodes"""
        if len(new_nodes) < 2:
            return
        
        # Get all nodes for the subject
        result = await db.execute(
            select(MindMapNode)
            .where(
                MindMapNode.user_id == user_id,
                MindMapNode.subject_id == subject_id
            )
        )
        all_nodes = list(result.scalars().all())
        
        # Simple heuristic: connect consecutive concepts from same session
        for i in range(len(new_nodes) - 1):
            edge = MindMapEdge(
                source_node_id=new_nodes[i].id,
                target_node_id=new_nodes[i + 1].id,
                relationship_type="related_to"
            )
            db.add(edge)
    
    async def update_node_mastery(
        self,
        db: AsyncSession,
        node_id: str,
        mastery_delta: float
    ) -> Optional[MindMapNode]:
        """
        Update node mastery level
        
        Args:
            db: Database session
            node_id: Node ID
            mastery_delta: Change in mastery (-1 to 1)
            
        Returns:
            Updated node
        """
        result = await db.execute(
            select(MindMapNode).where(MindMapNode.id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return None
        
        # Update mastery level
        new_mastery = max(0.0, min(1.0, node.mastery_level + mastery_delta))
        node.mastery_level = new_mastery
        
        # Update status based on mastery
        if new_mastery >= 0.7:
            node.status = "strong"
        elif new_mastery <= 0.3:
            node.status = "weak"
        else:
            node.status = "learning"
        
        await db.commit()
        await db.refresh(node)
        
        return node
    
    async def mark_weak_from_quiz(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str,
        weak_topics: List[str]
    ):
        """
        Mark nodes as weak based on quiz results
        
        Args:
            db: Database session
            user_id: User ID
            subject_id: Subject ID
            weak_topics: List of weak topic names
        """
        result = await db.execute(
            select(MindMapNode)
            .where(
                MindMapNode.user_id == user_id,
                MindMapNode.subject_id == subject_id
            )
        )
        nodes = result.scalars().all()
        
        for node in nodes:
            # Check if node matches any weak topic
            for topic in weak_topics:
                if topic.lower() in node.label.lower() or node.label.lower() in topic.lower():
                    node.mastery_level = max(0.0, node.mastery_level - 0.2)
                    node.status = "weak"
                    break
        
        await db.commit()
    
    async def get_weak_nodes(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str
    ) -> List[MindMapNode]:
        """Get all weak nodes for a subject"""
        result = await db.execute(
            select(MindMapNode)
            .where(
                MindMapNode.user_id == user_id,
                MindMapNode.subject_id == subject_id,
                MindMapNode.status == "weak"
            )
        )
        return list(result.scalars().all())
    
    async def auto_generate_from_sessions(
        self,
        db: AsyncSession,
        user_id: str,
        subject_id: str,
        max_nodes: int = 10
    ) -> List[MindMapNode]:
        """
        Auto-generate mindmap nodes from recent session concepts
        Uses regex fallback for reliable concept extraction
        """
        from app.models.session import Session, Message
        import re
        
        # Get recent sessions for this subject
        result = await db.execute(
            select(Session)
            .where(
                Session.user_id == user_id,
                Session.subject_id == subject_id
            )
            .order_by(Session.updated_at.desc())
            .limit(5)
        )
        sessions = result.scalars().all()
        
        if not sessions:
            return []
        
        # Extract concepts from assistant messages
        all_concepts = []
        for session in sessions:
            result = await db.execute(
                select(Message)
                .where(
                    Message.session_id == session.id,
                    Message.role == "assistant"
                )
                .order_by(Message.created_at.desc())
                .limit(3)
            )
            messages = result.scalars().all()
            
            for msg in messages:
                # Regex-based concept extraction (no LLM needed)
                text = msg.content[:1000]
                
                # Extract multi-word capitalized terms
                multi_word = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
                
                # Extract single capitalized words (min 3 chars)
                single_word = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
                
                # Filter common words
                exclude = {'The', 'This', 'That', 'These', 'Those', 'What', 'When', 
                          'Where', 'Why', 'How', 'Which', 'Who', 'And', 'But', 'For'}
                
                concepts = multi_word + [w for w in single_word if w not in exclude]
                all_concepts.extend(concepts)
        
        # Get unique concepts
        unique_concepts = list(dict.fromkeys(all_concepts))[:max_nodes]
        
        if not unique_concepts:
            # Fallback: create a default node for the subject
            unique_concepts = ["Getting Started"]
        
        # Create nodes with spiral layout
        nodes = []
        for i, concept in enumerate(unique_concepts):
            angle = i * 0.8
            radius = 150 + (i // 6) * 100
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            node = MindMapNode(
                subject_id=subject_id,
                user_id=user_id,
                label=concept,
                x_position=x,
                y_position=y,
                mastery_level=0.2,  # Default low mastery
                status="learning"
            )
            db.add(node)
            nodes.append(node)
        
        # Commit nodes
        if nodes:
            await db.commit()
            for node in nodes:
                await db.refresh(node)
        
        return nodes


# Global instance
mindmap_service = MindMapService()
