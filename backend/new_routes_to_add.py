"""
New API Routes for Topic-by-Topic Teaching
Add these routes to backend/app/routes/teacher.py before the last line
"""

@router.get("/roadmap/{roadmap_id}/module/{module_id}/topic/{topic_index}")
async def get_topic_content(
    roadmap_id: str,
    module_id: str,
    topic_index: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed teaching content for a specific topic"""
    # Verify ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    if not roadmap_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    # Get lesson state
    lesson_state_result = await db.execute(
        select(TeacherLessonState).where(TeacherLessonState.module_id == module_id)
    )
    lesson_state = lesson_state_result.scalar_one_or_none()
    
    # Generate topic content
    topic_data = await teacher_service.generate_topic_content(module_id, topic_index, db)
    
    return {
        "topic_index": topic_index,
        "topic_data": topic_data,
        "current_topic_index": lesson_state.current_topic_index if lesson_state else 0
    }


@router.post("/roadmap/{roadmap_id}/module/{module_id}/topic/{topic_index}/complete")
async def complete_topic_route(
    roadmap_id: str,
    module_id: str,
    topic_index: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark current topic as completed and get next topic info"""
    # Verify ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    if not roadmap_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    # Complete topic
    result = await teacher_service.complete_topic(module_id, topic_index, db)
    
    return result


@router.post("/roadmap/{roadmap_id}/module/{module_id}/topic/{topic_index}/ask")
async def ask_topic_question_route(
    roadmap_id: str,
    module_id: str,
    topic_index: int,
    request: TeachChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ask a question about the current topic"""
    # Verify ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    if not roadmap_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    # Get answer
    answer = await teacher_service.answer_topic_question(module_id, topic_index, request.message, db)
    
    return {"answer": answer}
