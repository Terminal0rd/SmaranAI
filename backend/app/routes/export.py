"""
Export API routes for PDF and PPT generation
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.session import Session, Message, SessionConcept
from app.models.user import User
from app.utils.security import get_current_user
from app.services.export_service import export_service

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/{session_id}/pdf")
async def export_session_pdf(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a session as PDF"""
    # Get session
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = [
        {"role": m.role, "content": m.content}
        for m in result.scalars().all()
    ]
    
    # Get concepts
    result = await db.execute(
        select(SessionConcept)
        .where(SessionConcept.session_id == session_id)
    )
    concepts = [c.concept_name for c in result.scalars().all()]
    
    # Generate PDF
    pdf_bytes = export_service.generate_pdf(
        title=session.title or "Learning Session",
        messages=messages,
        concepts=concepts
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{session.title or "session"}.pdf"'
        }
    )


@router.get("/{session_id}/pptx")
async def export_session_pptx(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a session as PowerPoint"""
    # Get session
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = [
        {"role": m.role, "content": m.content}
        for m in result.scalars().all()
    ]
    
    # Get concepts
    result = await db.execute(
        select(SessionConcept)
        .where(SessionConcept.session_id == session_id)
    )
    concepts = [c.concept_name for c in result.scalars().all()]
    
    # Generate PPTX
    pptx_bytes = export_service.generate_pptx(
        title=session.title or "Learning Session",
        messages=messages,
        concepts=concepts
    )
    
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{session.title or "session"}.pptx"'
        }
    )
