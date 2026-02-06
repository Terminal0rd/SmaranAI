"""
API Routes for SmaranAI
"""
from app.routes.auth import router as auth_router
from app.routes.subjects import router as subjects_router
from app.routes.sessions import router as sessions_router
from app.routes.chat import router as chat_router
from app.routes.mindmap import router as mindmap_router
from app.routes.quiz import router as quiz_router
from app.routes.progress import router as progress_router
from app.routes.documents import router as documents_router
from app.routes.export import router as export_router
from app.routes.teacher import router as teacher_router

__all__ = [
    "auth_router",
    "subjects_router",
    "sessions_router",
    "chat_router",
    "mindmap_router",
    "quiz_router",
    "progress_router",
    "documents_router",
    "export_router",
    "teacher_router",
]
