"""
MindMap models
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MindMapNode(Base):
    """Concept node in mind map"""
    __tablename__ = "mindmap_nodes"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Position for visualization
    x_position: Mapped[float] = mapped_column(Float, default=0.0)
    y_position: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Mastery tracking
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1 scale
    status: Mapped[str] = mapped_column(String(20), default="learning")  # learning, weak, strong
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="mindmap_nodes")
    user = relationship("User", back_populates="mindmap_nodes")
    
    # Edges where this node is the source
    outgoing_edges = relationship(
        "MindMapEdge", 
        foreign_keys="MindMapEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan"
    )
    # Edges where this node is the target
    incoming_edges = relationship(
        "MindMapEdge", 
        foreign_keys="MindMapEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan"
    )


class MindMapEdge(Base):
    """Relationship between concept nodes"""
    __tablename__ = "mindmap_edges"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    source_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("mindmap_nodes.id"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("mindmap_nodes.id"), nullable=False)
    
    relationship_type: Mapped[str] = mapped_column(String(50), default="related_to")  # related_to, prerequisite, extends
    
    # Relationships
    source_node = relationship("MindMapNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("MindMapNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
