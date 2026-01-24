"""
MindMap API routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.mindmap import (
    MindMapResponse, MindMapNodeResponse, MindMapNodeUpdate, MindMapEdgeResponse
)
from app.utils.security import get_current_user
from app.services.mindmap_service import mindmap_service

router = APIRouter(prefix="/api/mindmap", tags=["MindMap"])


@router.get("/{subject_id}", response_model=MindMapResponse)
async def get_mindmap(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the complete mind map for a subject"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"GET mindmap for subject={subject_id}, user={current_user.id} ({current_user.email})")
    
    nodes, edges = await mindmap_service.get_mindmap(
        db, current_user.id, subject_id
    )
    
    logger.info(f"Found {len(nodes)} nodes and {len(edges)} edges in DB")
    
    # Auto-generate mindmap if empty
    if not nodes:
        logger.info(f"No mindmap found for subject {subject_id}, auto-generating...")
        
        nodes = await mindmap_service.auto_generate_from_sessions(
            db, current_user.id, subject_id
        )
        logger.info(f"Auto-generated {len(nodes)} nodes")
        
        # Edges will be empty for now (can add auto-linking later)
        edges = []
    
    return MindMapResponse(
        subject_id=subject_id,
        nodes=[MindMapNodeResponse.model_validate(n) for n in nodes],
        edges=[MindMapEdgeResponse.model_validate(e) for e in edges]
    )


@router.get("/{subject_id}/weak-nodes", response_model=List[MindMapNodeResponse])
async def get_weak_nodes(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all weak concept nodes for a subject"""
    nodes = await mindmap_service.get_weak_nodes(
        db, current_user.id, subject_id
    )
    return [MindMapNodeResponse.model_validate(n) for n in nodes]


@router.put("/node/{node_id}", response_model=MindMapNodeResponse)
async def update_node(
    node_id: str,
    updates: MindMapNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a mind map node (position, mastery, etc.)"""
    from sqlalchemy import select
    from app.models.mindmap import MindMapNode
    
    # Verify ownership
    result = await db.execute(
        select(MindMapNode).where(
            MindMapNode.id == node_id,
            MindMapNode.user_id == current_user.id
        )
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Update fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(node, field, value)
    
    # Update status based on mastery
    if 'mastery_level' in update_data:
        if node.mastery_level >= 0.7:
            node.status = "strong"
        elif node.mastery_level <= 0.3:
            node.status = "weak"
        else:
            node.status = "learning"
    
    await db.commit()
    await db.refresh(node)
    
    return MindMapNodeResponse.model_validate(node)
