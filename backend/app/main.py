"""
SmaranAI Backend - FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings
from app.database import init_db
from app.routes import (
    auth_router,
    subjects_router,
    sessions_router,
    chat_router,
    mindmap_router,
    quiz_router,
    progress_router,
    documents_router
)
from app.routes.export import router as export_router
from app.routes.teacher import router as teacher_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting SmaranAI Backend...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Create storage directories
    from pathlib import Path
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.vector_store_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Storage directories created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SmaranAI Backend...")


# Create FastAPI app
app = FastAPI(
    title="SmaranAI API",
    description="AI Tutor API with MindMap-First Learning, Whiteboard Sessions, and Adaptive Quiz Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(auth_router)
app.include_router(subjects_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(mindmap_router)
app.include_router(quiz_router)
app.include_router(progress_router)
app.include_router(documents_router)
app.include_router(export_router)
app.include_router(teacher_router)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.services.llm_service import llm_service
    
    llm_healthy = await llm_service.health_check()
    
    return {
        "status": "healthy",
        "service": "SmaranAI API",
        "llm_connected": llm_healthy
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SmaranAI API",
        "docs": "/docs",
        "health": "/health"
    }


# LLM status check endpoint
@app.get("/api/llm/status")
async def llm_status():
    """Check LLM server status"""
    from app.services.llm_service import llm_service
    
    is_healthy = await llm_service.health_check()
    
    return {
        "connected": is_healthy,
        "url": settings.llm_server_url
    }
