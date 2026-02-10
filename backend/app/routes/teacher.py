"""
Teacher Mode API Routes
RESTful endpoints for teacher-guided learning system
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.teacher import TeacherRoadmap, TeacherModule, TeacherLessonState, TeacherMemoryCard
from app.schemas.teacher import (
    RoadmapCreate, RoadmapResponse, RoadmapListResponse,
    ModuleResponse, ModuleDetailResponse,
    TeachContentResponse, CheckQuestionsResponse,
    CheckSubmission, CheckResultResponse,
    ReteachRequest, ReteachContentResponse,
    MemoryCardsResponse,
    TeachChatRequest, TeachChatResponse
)
from app.utils.security import get_current_user
from app.services.teacher_service import teacher_service

router = APIRouter(prefix="/api/teacher", tags=["Teacher Mode"])


@router.post("/roadmap/create", response_model=RoadmapResponse)
async def create_roadmap(
    data: RoadmapCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a new AI-powered learning roadmap
    Creates 8-15 modules with structured objectives and topics
    """
    roadmap = await teacher_service.generate_roadmap(
        subject=data.subject,
        goal=data.goal,
        user_id=current_user.id,
        db=db
    )
    
    # Fetch full roadmap with modules
    result = await db.execute(
        select(TeacherRoadmap)
        .where(TeacherRoadmap.id == roadmap.id)
        .options(selectinload(TeacherRoadmap.modules))
    )
    roadmap = result.scalar_one()
    
    return roadmap


@router.get("/roadmap", response_model=List[RoadmapListResponse])
async def get_all_roadmaps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all roadmaps for current user
    Returns simplified list view
    """
    result = await db.execute(
        select(TeacherRoadmap)
        .where(TeacherRoadmap.user_id == current_user.id)
        .order_by(TeacherRoadmap.created_at.desc())
    )
    roadmaps = result.scalars().all()
    
    return [
        RoadmapListResponse(
            id=r.id,
            subject=r.subject,
            goal=r.goal,
            total_modules=r.total_modules,
            completed_modules=r.completed_modules,
            overall_progress=r.overall_progress,
            created_at=r.created_at
        )
        for r in roadmaps
    ]


@router.get("/roadmap/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete roadmap with all modules
    Shows progress, lock states, and mastery scores
    """
    result = await db.execute(
        select(TeacherRoadmap)
        .where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
        .options(selectinload(TeacherRoadmap.modules))
    )
    roadmap = result.scalar_one_or_none()
    
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found"
        )
    
    return roadmap


@router.get("/roadmap/{roadmap_id}/module/{module_id}", response_model=ModuleDetailResponse)
async def get_module_detail(
    roadmap_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed module information
    Includes current phase, attempts, and mastery status
    """
    # Verify roadmap ownership
    roadmap_result = await db.execute(
        select(TeacherRoadmap).where(
            TeacherRoadmap.id == roadmap_id,
            TeacherRoadmap.user_id == current_user.id
        )
    )
    roadmap = roadmap_result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    
    # Get module with lesson state
    module_result = await db.execute(
        select(TeacherModule)
        .where(TeacherModule.id == module_id)
        .options(selectinload(TeacherModule.lesson_state))
    )
    module = module_result.scalar_one_or_none()
    
    if not module or module.roadmap_id != roadmap_id:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Build response
    lesson_state = module.lesson_state
    
    return ModuleDetailResponse(
        id=module.id,
        module_index=module.module_index,
        title=module.title,
        level=module.level.value,
        objectives=module.objectives,
        topics=module.topics,
        prerequisites=module.prerequisites,
        estimated_minutes=module.estimated_minutes,
        status=module.status.value,
        mastery_score=module.mastery_score,
        current_phase=lesson_state.current_phase.value if lesson_state else None,
        check_attempts=lesson_state.check_attempts if lesson_state else 0,
        can_retry=lesson_state.check_attempts < lesson_state.max_attempts if lesson_state else True
    )


@router.post("/roadmap/{roadmap_id}/module/{module_id}/teach")
async def generate_teach_content(
    roadmap_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate whiteboard-style teaching content
    Uses RAG for accuracy, returns structured sections
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
    
    # Generate content
    teach_data = await teacher_service.generate_teach_content(module_id, db)
    
    # Get module title
    module_result = await db.execute(
        select(TeacherModule).where(TeacherModule.id == module_id)
    )
    module = module_result.scalar_one()
    
    return TeachContentResponse(
        module_title=module.title,
        sections=teach_data["sections"],
        summary=teach_data["sections"][-1]["content"] if teach_data["sections"] else ""
    )


@router.post("/roadmap/{roadmap_id}/module/{module_id}/check/generate", response_model=CheckQuestionsResponse)
async def generate_check_questions(
    roadmap_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate check phase questions
    2-5 questions to verify mastery
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
    
    # Generate questions
    questions = await teacher_service.generate_check_questions(module_id, db)
    
    return CheckQuestionsResponse(
        module_id=module_id,
        questions=questions
    )


@router.post("/roadmap/{roadmap_id}/module/{module_id}/check/submit", response_model=CheckResultResponse)
async def submit_check_answers(
    roadmap_id: str,
    module_id: str,
    submission: CheckSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit check answers for grading
    Returns score, passed/failed, and weak topics
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
    
    # Get stored questions from lesson state to avoid regeneration bug
    lesson_state_result = await db.execute(
        select(TeacherLessonState).where(TeacherLessonState.module_id == module_id)
    )
    lesson_state = lesson_state_result.scalar_one_or_none()
    
    # Use stored questions if available, otherwise regenerate (backward compat)
    if lesson_state and lesson_state.check_questions:
        questions = lesson_state.check_questions
    else:
        questions = await teacher_service.generate_check_questions(module_id, db)
    
    # Grade answers
    score, passed, weak_topics, grading_details = await teacher_service.grade_check_answers(
        module_id=module_id,
        user_id=current_user.id,
        questions=questions,
        answers=[ans.dict() for ans in submission.answers],
        db=db
    )
    
    return CheckResultResponse(
        score=score,
        passed=passed,
        weak_topics=weak_topics if weak_topics else None,
        grading_details=grading_details,
        next_action="next_module" if passed else "reteach"
    )


@router.post("/roadmap/{roadmap_id}/module/{module_id}/reteach", response_model=ReteachContentResponse)
async def generate_reteach_content(
    roadmap_id: str,
    module_id: str,
    request: ReteachRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate simplified reteach content for weak topics
    Includes practice questions
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
    
    # Generate reteach content
    reteach_data = await teacher_service.generate_reteach_content(
        module_id=module_id,
        weak_topics=request.weak_topics,
        db=db
    )
    
    return ReteachContentResponse(
        weak_topics=request.weak_topics,
        explanations=reteach_data["explanations"],
        practice_questions=reteach_data.get("practice_questions", [])
    )


@router.get("/roadmap/{roadmap_id}/module/{module_id}/memory-cards", response_model=MemoryCardsResponse)
async def get_memory_cards(
    roadmap_id: str,
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get memory cards for a mastered module
    Returns 3-7 retention flashcards
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
    
    # Generate/get memory cards
    cards = await teacher_service.generate_memory_cards(module_id, db)
    
    # Get module title
    module_result = await db.execute(
        select(TeacherModule).where(TeacherModule.id == module_id)
    )
    module = module_result.scalar_one()
    
    return MemoryCardsResponse(
        module_id=module_id,
        module_title=module.title,
        cards=cards
    )


@router.post("/roadmap/{roadmap_id}/module/{module_id}/chat", response_model=TeachChatResponse)
async def teach_chat(
    roadmap_id: str,
    module_id: str,
    request: TeachChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Interactive Q&A during teaching phase
    Student can ask questions and get AI-powered answers
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
    
    # Answer question
    answer = await teacher_service.answer_teach_question(
        module_id=module_id,
        question=request.message,
        db=db
    )
    
    return TeachChatResponse(response=answer)
