"""
MindMap schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MindMapNodeBase(BaseModel):
    """Base node schema"""
    label: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class MindMapNodeCreate(MindMapNodeBase):
    """Create node schema"""
    subject_id: str
    x_position: float = 0.0
    y_position: float = 0.0


class MindMapNodeUpdate(BaseModel):
    """Update node schema"""
    label: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    mastery_level: Optional[float] = Field(None, ge=0.0, le=1.0)


class MindMapNodeResponse(MindMapNodeBase):
    """Node response schema"""
    id: str
    subject_id: str
    user_id: str
    x_position: float
    y_position: float
    mastery_level: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MindMapEdgeResponse(BaseModel):
    """Edge response schema"""
    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str

    class Config:
        from_attributes = True


class MindMapResponse(BaseModel):
    """Complete mindmap response"""
    subject_id: str
    nodes: List[MindMapNodeResponse]
    edges: List[MindMapEdgeResponse]
