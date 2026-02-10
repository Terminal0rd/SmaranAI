"""
New API Routes for Conversational Teacher Mode  
Add to backend/app/routes/teacher.py
"""

from app.services.conversational_teacher_service import conversational_teacher_service
from app.models.teacher import ConversationTurn, ConceptMastery


@router.post("/roadmap/{roadmap_id}/module/{module_id}/teach/start")
async def start_teaching_conversation(
    roadmap_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a conversational teaching session for a module
    Returns AI's opening message
    """
    # Verify ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    if not roadmap_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    result = await conversational_teacher_service.start_teaching(
        module_id=module_id,
        user_id=current_user.id,
        db=db
    )
    
    return result


@router.post("/roadmap/{roadmap_id}/module/{module_id}/teach/respond")
async def respond_in_teaching(
    roadmap_id: str,
    module_id: str,
    request: dict,  # {"message": "student's response"}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Student sends a message, AI responds
    Core of the conversational loop
    """
    # Verify ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    if not roadmap_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    student_message = request.get("message", "")
    
    result = await conversational_teacher_service.respond_to_student(
        module_id=module_id,
        user_id=current_user.id,
        student_message=student_message,
        db=db
    )
    
    return result


@router.get("/roadmap/{roadmap_id}/module/{module_id}/teach/history")
async def get_conversation_history(
    roadmap_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full conversation history for a module
    """
    # Verify ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    if not roadmap_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    # Get turns
    turns_result = await db.execute(
        select(ConversationTurn)
        .where(
            ConversationTurn.module_id == module_id,
            ConversationTurn.user_id == current_user.id
        )
        .order_by(ConversationTurn.turn_index)
    )
    turns = turns_result.scalars().all()
    
    return {
        "turns": [
            {
                "speaker": turn.speaker,
                "message": turn.message,
                "concept": turn.concept_tag,
                "timestamp": turn.created_at.isoformat()
            }
            for turn in turns
        ]
    }


@router.get("/roadmap/{roadmap_id}/module/{module_id}/teach/progress")
async def get_teaching_progress(
    roadmap_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get concept mastery progress
    """
    # Verify ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    if not roadmap_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    # Get mastery
    mastery_result = await db.execute(
        select(ConceptMastery).where(
            ConceptMastery.module_id == module_id,
            ConceptMastery.user_id == current_user.id
        )
    )
    masteries = mastery_result.scalars().all()
    
    return {
        "concepts": [
            {
                "name": m.concept,
                "mastery_score": m.mastery_score,
                "attempts": m.attempts,
                "is_mastered": m.mastery_score >= 0.7
            }
            for m in masteries
        ]
    }
