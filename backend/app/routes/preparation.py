"""
Preparation Mode Routes
API endpoints for AI Semester Preparation Engine
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.models.user import User
from app.utils.security import get_current_user  # FIXED: correct import path
from app.services.preparation_service import preparation_service
from app.schemas.preparation import PreparationRequest, PreparationResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/preparation", tags=["preparation"])


@router.post("/generate", response_model=PreparationResponse)
async def generate_preparation(
    request: PreparationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate initial semester preparation (syllabus only - fast load)
    
    SMART CACHING: If a preparation already exists for this user+subject,
    returns the existing one instead of regenerating.
    """
    from app.models.preparation import Preparation
    from sqlalchemy import select, func
    
    try:
        logger.info(f"User {current_user.id} requesting preparation for {request.subject}")
        
        # STEP 1: Check if preparation already exists for this user + subject (case-insensitive)
        existing_query = (
            select(Preparation)
            .where(
                Preparation.user_id == current_user.id,
                func.lower(Preparation.subject) == request.subject.strip().lower()
            )
            .order_by(Preparation.updated_at.desc())
            .limit(1)
        )
        existing_result = await db.execute(existing_query)
        existing_prep = existing_result.scalar_one_or_none()
        
        if existing_prep and existing_prep.content:
            # Check if it has at least a syllabus (minimum valid preparation)
            content = existing_prep.content
            has_syllabus = content.get("syllabus") and len(content.get("syllabus", [])) > 0
            
            if has_syllabus:
                logger.info(f"Found existing preparation ID {existing_prep.id} for '{request.subject}', returning cached version")
                return {
                    **content,
                    "id": existing_prep.id,
                    "subject": existing_prep.subject,
                    "university": existing_prep.university,
                    "exam_type": existing_prep.exam_type,
                    "exam_date": existing_prep.exam_date,
                }
        
        # STEP 2: No existing preparation found — generate new one
        logger.info(f"No existing preparation found for '{request.subject}', generating new...")
        
        # Generate initial preparation (syllabus only)
        result = await preparation_service.generate_preparation(
            subject=request.subject,
            university=request.university,
            exam_type=request.exam_type or "Regular",
            exam_date=request.exam_date,
            db=db,
            use_rag=request.use_rag if request.use_rag is not None else True
        )
        
        # Save to database
        prep_id = await preparation_service.save_preparation(
            user_id=current_user.id,
            subject=request.subject,
            university=request.university,
            exam_type=request.exam_type or "Regular",
            exam_date=request.exam_date,
            content=result,
            db=db
        )
        
        logger.info(f"Preparation generated and saved with ID: {prep_id}")
        
        # Return with ID for frontend tracking
        return {**result, "id": prep_id}
        
    except Exception as e:
        logger.error(f"Preparation generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preparation: {str(e)}"
        )


@router.post("/generate-section")
async def generate_section(
    section: str,
    subject: str,
    university: str,
    exam_type: str,
    prep_id: int | None = None,  # Optional for debugging
    exam_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a specific section on-demand (progressive loading)
    
    Sections:
    - notes: Smart notes for topics
    - questions: 5M, 10M, and predicted questions
    - mock_viva: Mock test and viva questions
    - ppt_plan: PPT content and study plan
    """
    try:
        logger.info(f"Section request - prep_id: {prep_id}, section: {section}, subject: {subject}")
        logger.info(f"User {current_user.id} requesting section '{section}' for {subject}")
        
        # STEP 1: Check if this section already exists in the database
        if prep_id:
            from app.models.preparation import Preparation
            from sqlalchemy import select as sel
            
            query = sel(Preparation).where(Preparation.id == prep_id, Preparation.user_id == current_user.id)
            db_result = await db.execute(query)
            existing_prep = db_result.scalar_one_or_none()
            
            if existing_prep and existing_prep.content:
                content = existing_prep.content
                
                # Map section name to content keys and check if they have real data
                section_keys_map = {
                    "notes": ["notes"],
                    "questions": ["five_mark_questions", "ten_mark_questions", "predicted_questions"],
                    "mock_viva": ["mock_test", "viva_questions"],
                    "ppt_plan": ["ppt_content", "study_plan"],
                }
                
                keys_to_check = section_keys_map.get(section, [])
                has_existing_data = False
                
                for key in keys_to_check:
                    val = content.get(key)
                    if isinstance(val, list) and len(val) > 0:
                        has_existing_data = True
                        break
                    if isinstance(val, dict) and len(val) > 0:
                        has_existing_data = True
                        break
                
                if has_existing_data:
                    logger.info(f"Section '{section}' already exists in DB for prep {prep_id}, returning cached version")
                    # Return only the relevant keys for this section
                    cached_result = {key: content.get(key, [] if key != "mock_test" else {}) for key in keys_to_check}
                    return cached_result
        
        # STEP 2: Section not in DB or empty — generate it
        logger.info(f"Section '{section}' not found in DB, generating fresh...")
        
        # Generate requested section
        result = await preparation_service.generate_section(
            section=section,
            subject=subject,
            university=university,
            exam_type=exam_type or "Regular",
            exam_date=exam_date,
            db=db,
            use_rag=True
        )
        
        # Only save to DB if result has actual content (not empty/error)
        def has_real_content(data: dict) -> bool:
            """Check if the result has real generated content, not just empty arrays"""
            if "error" in data:
                return False
            for key, value in data.items():
                if key == "error":
                    continue
                if isinstance(value, list) and len(value) > 0:
                    return True
                if isinstance(value, dict) and len(value) > 0:
                    return True
            return False
        
        # Update preparation in database (if prep_id provided AND content is valid)
        if prep_id and has_real_content(result):
            await preparation_service.update_preparation_section(
                prep_id=prep_id,
                section_data={k: v for k, v in result.items() if k != "error"},
                db=db
            )
            logger.info(f"Section '{section}' generated and saved for prep {prep_id}")
        elif prep_id and not has_real_content(result):
            logger.warning(f"Section '{section}' result is empty/error, NOT saving to DB")
        else:
            logger.warning(f"No prep_id provided, section '{section}' not saved to database")
        
        return result
        
    except Exception as e:
        logger.error(f"Section generation failed: {e}", exc_info=True)
        
        # GRACEFUL FALLBACK: Return 200 with error message instead of 500
        # This prevents frontend crashes and allows retry
        error_message = "Generation took longer than expected. Please try again or reduce complexity."
        
        # Return appropriate empty structure based on section
        if section == "notes":
            return {
                "notes": [],
                "error": error_message
            }
        elif section == "questions":
            return {
                "five_mark_questions": [],
                "ten_mark_questions": [],
                "predicted_questions": [],
                "error": error_message
            }
        elif section == "mock_viva":
            return {
                "mock_test": {},
                "viva_questions": [],
                "error": error_message
            }
        elif section == "ppt_plan":
            return {
                "ppt_content": [],
                "study_plan": [],
                "error": error_message
            }
        else:
            return {"error": error_message}


@router.get("/history")
async def get_preparation_history(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's preparation history"""
    from app.models.preparation import Preparation
    from sqlalchemy import select, func
    
    # Get preparations
    query = (
        select(Preparation)
        .where(Preparation.user_id == current_user.id)
        .order_by(Preparation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    preparations = result.scalars().all()
    
    # Get total count
    count_query = select(func.count()).select_from(Preparation).where(Preparation.user_id == current_user.id)
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return {
        "preparations": [
            {
                "id": p.id,
                "subject": p.subject,
                "university": p.university,
                "exam_type": p.exam_type,
                "exam_date": p.exam_date,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
                "has_notes": bool(p.content.get("notes")),
                "has_questions": bool(p.content.get("five_mark_questions") or p.content.get("ten_mark_questions")),
                "has_predicted": bool(p.content.get("predicted_questions")),
                "has_mock": bool(p.content.get("mock_test")),
                "has_viva": bool(p.content.get("viva_questions")),
                "has_ppt": bool(p.content.get("ppt_content")),
                "has_plan": bool(p.content.get("study_plan")),
            }
            for p in preparations
        ],
        "total": total
    }


@router.get("/history/{prep_id}")
async def get_preparation_by_id(
    prep_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific preparation by ID with full content"""
    from app.models.preparation import Preparation
    from sqlalchemy import select
    
    query = select(Preparation).where(
        Preparation.id == prep_id,
        Preparation.user_id == current_user.id
    )
    
    result = await db.execute(query)
    prep = result.scalar_one_or_none()
    
    if not prep:
        raise HTTPException(status_code=404, detail="Preparation not found")
    
    # Return full content with metadata
    return {
        **prep.content,
        "id": prep.id,
        "subject": prep.subject,
        "university": prep.university,
        "exam_type": prep.exam_type,
        "exam_date": prep.exam_date,
        "created_at": prep.created_at.isoformat(),
        "updated_at": prep.updated_at.isoformat(),
    }


@router.delete("/history/{prep_id}")
async def delete_preparation(
    prep_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a preparation from history"""
    from app.models.preparation import Preparation
    from sqlalchemy import delete
    
    query = delete(Preparation).where(
        Preparation.id == prep_id,
        Preparation.user_id == current_user.id
    )
    
    result = await db.execute(query)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Preparation not found")
    
    return {"message": "Preparation deleted successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "preparation"}
