"""
Document upload API routes
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import get_settings
from app.models.document import Document, DocumentChunk
from app.models.subject import Subject
from app.models.user import User
from app.schemas.document import (
    DocumentUploadResponse, DocumentResponse, DocumentListResponse, ProcessingStatusResponse
)
from app.utils.security import get_current_user
from app.utils.pdf_parser import extract_text_from_pdf, validate_pdf
from app.utils.text_chunker import chunk_text
from app.services.embedding_service import embedding_service

settings = get_settings()
router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = Path(settings.upload_dir)
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024


async def process_document(
    document_id: str,
    file_path: str,
    subject_id: str,
    filename: str
):
    """Background task to process uploaded document"""
    from app.database import AsyncSessionLocal
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"[PDF Processing] Starting for document {document_id}: {filename}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Extract text from PDF
            logger.info(f"[PDF Processing] Extracting text from {filename}")
            text = extract_text_from_pdf(file_path)
            
            # Check if text is empty
            if not text or len(text.strip()) < 50:
                logger.error(f"[PDF Processing] FAILED - No readable text in {filename}")
                result = await db.execute(
                    select(Document).where(Document.id == document_id)
                )
                document = result.scalar_one_or_none()
                if document:
                    document.is_processed = False
                await db.commit()
                return
            
            logger.info(f"[PDF Processing] Extracted {len(text)} characters")
            
            # CRITICAL: Limit text size BEFORE chunking to prevent MemoryError
            # Using aggressive limit for low-memory laptops
            MAX_TEXT_SIZE = 30000  # 30K chars - good balance
            if len(text) > MAX_TEXT_SIZE:
                logger.warning(f"[PDF Processing] Text too large ({len(text)} chars) - truncating to {MAX_TEXT_SIZE} chars")
                text = text[:MAX_TEXT_SIZE]
            
            # Use SIMPLE chunking to avoid memory issues
            # No overlap, no fancy sentence detection - just split every 400 chars
            try:
                logger.info(f"[PDF Processing] Starting simple chunking...")
                chunk_size = 400
                chunks = []
                
                # Simple split - much more memory efficient
                for i in range(0, len(text), chunk_size):
                    chunk = text[i:i + chunk_size].strip()
                    if chunk and len(chunk) > 50:  # Only keep meaningful chunks
                        chunks.append(chunk)
                    
                    # Log progress every 20 chunks
                    if len(chunks) % 20 == 0:
                        logger.info(f"[PDF Processing] Chunked {len(chunks)} pieces so far...")
                
                logger.info(f"[PDF Processing] Created {len(chunks)} chunks")
                
            except MemoryError:
                logger.error(f"[PDF Processing] FAILED - Out of memory. Close other applications and try again.")
                return
            except Exception as e:
                logger.error(f"[PDF Processing] FAILED - Chunking error: {e}")
                return
            
            if not chunks:
                logger.error(f"[PDF Processing] FAILED - No chunks created from {filename}")
                return
            
            # Generate embeddings and store
            logger.info(f"[PDF Processing] Generating embeddings for {len(chunks)} chunks")
            embedding_ids = embedding_service.add_documents(
                chunks=chunks,
                document_id=document_id,
                subject_id=subject_id,
                filename=filename
            )
            logger.info(f"[PDF Processing] Generated {len(embedding_ids)} embeddings")
            
            # Save chunks to database
            for i, (chunk, emb_id) in enumerate(zip(chunks, embedding_ids)):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk,
                    embedding_id=emb_id
                )
                db.add(chunk_record)
            
            # Mark document as processed
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            if document:
                document.is_processed = True
            
            await db.commit()
            logger.info(f"[PDF Processing] SUCCESS - {filename} fully processed")
            logger.info(f"[Vector Store] Saved to disk with {len(embedding_ids)} new embeddings")
            
        except Exception as e:
            logger.error(f"[PDF Processing] FAILED for {document_id}: {str(e)}", exc_info=True)
            # Document remains with is_processed=False


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subject_id: Optional[str] = Form(None),  # ← NOW OPTIONAL
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a PDF document for RAG
    **NEW**: Auto-classifies subject if not provided
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    stored_filename = f"{file_id}.pdf"
    
    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path = UPLOAD_DIR / stored_filename
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Validate PDF
    if not validate_pdf(str(file_path)):
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    
    # AUTO-CLASSIFY if subject_id not provided
    if not subject_id:
        from app.services.subject_classifier import subject_classifier
        
        logger.info(f"[Auto-Classify] No subject provided for {file.filename}, classifying...")
        
        # Extract sample text for classification
        try:
            sample_text = extract_text_from_pdf(str(file_path))
            sample_text = sample_text[:1500] if sample_text else ""
        except Exception as e:
            logger.warning(f"[Auto-Classify] Failed to extract text: {e}")
            sample_text = ""
        
        # Get available subjects
        result = await db.execute(select(Subject))
        available_subjects = result.scalars().all()
        
        if not available_subjects:
            raise HTTPException(
                status_code=500,
                detail="No subjects available. Please create a subject first or contact admin."
            )
        
        # Classify
        classified_subject_id, confidence = await subject_classifier.classify_document(
            sample_text,
            available_subjects
        )
        
        if not classified_subject_id:
            raise HTTPException(
                status_code=500,
                detail="Could not classify document. Please select subject manually."
            )
        
        subject_id = classified_subject_id
        
        # Get subject name for logging
        classified_subject = next((s for s in available_subjects if s.id == subject_id), None)
        logger.info(
            f"[Auto-Classify] {file.filename} → {classified_subject.name if classified_subject else 'Unknown'} "
            f"(confidence: {confidence:.2f})"
        )
    
    # Validate subject (whether manual or auto-classified)
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Create document record
    document = Document(
        uploader_id=current_user.id,
        subject_id=subject_id,
        filename=stored_filename,
        original_name=file.filename,
        file_size=file_size,
        is_processed=False
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Start background processing
    background_tasks.add_task(
        process_document,
        document.id,
        str(file_path),
        subject_id,
        file.filename
    )
    
    return DocumentUploadResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    subject_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all uploaded documents"""
    query = select(Document)
    
    if subject_id:
        query = query.where(Document.subject_id == subject_id)
    
    query = query.order_by(Document.uploaded_at.desc())
    result = await db.execute(query)
    documents = result.scalars().all()
    
    doc_responses = []
    for doc in documents:
        # Count chunks
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        chunks_count = len(result.scalars().all())
        
        doc_response = DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            original_name=doc.original_name,
            file_size=doc.file_size,
            subject_id=doc.subject_id,
            is_processed=doc.is_processed,
            uploaded_at=doc.uploaded_at,
            chunks_count=chunks_count
        )
        doc_responses.append(doc_response)
    
    return DocumentListResponse(documents=doc_responses, total=len(doc_responses))


@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document processing status"""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Count chunks
    result = await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    chunks = result.scalars().all()
    
    status_message = "Processed successfully" if document.is_processed else "Processing..."
    
    return ProcessingStatusResponse(
        document_id=document_id,
        is_processed=document.is_processed,
        chunks_count=len(chunks),
        status_message=status_message
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its embeddings"""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.uploader_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    file_path = UPLOAD_DIR / document.filename
    if file_path.exists():
        os.remove(file_path)
    
    # Delete from vector store
    embedding_service.delete_document(document_id)
    
    # Delete from database (cascades to chunks)
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}
