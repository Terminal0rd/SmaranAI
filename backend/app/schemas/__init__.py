"""
Schemas for SmaranAI API
"""
from app.schemas.user import (
    UserCreate, UserLogin, UserUpdate, UserResponse, Token, TokenData
)
from app.schemas.subject import (
    SubjectCreate, SubjectUpdate, SubjectResponse
)
from app.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionWithMessages,
    MessageCreate, MessageResponse, ConceptResponse
)
from app.schemas.chat import (
    ChatRequest, ChatResponse, SourceReference, YouTubeRecommendation
)
from app.schemas.mindmap import (
    MindMapNodeCreate, MindMapNodeUpdate, MindMapNodeResponse,
    MindMapEdgeResponse, MindMapResponse
)
from app.schemas.quiz import (
    QuizGenerateRequest, QuizGenerateResponse, QuizQuestionResponse,
    QuizSubmitRequest, QuizResultResponse, QuizAttemptResponse
)
from app.schemas.progress import (
    SubjectProgressResponse, OverallProgressResponse, DashboardDataResponse
)
from app.schemas.document import (
    DocumentUploadResponse, DocumentResponse, DocumentListResponse,
    ProcessingStatusResponse
)

__all__ = [
    # User
    "UserCreate", "UserLogin", "UserUpdate", "UserResponse", "Token", "TokenData",
    # Subject
    "SubjectCreate", "SubjectUpdate", "SubjectResponse",
    # Session
    "SessionCreate", "SessionUpdate", "SessionResponse", "SessionWithMessages",
    "MessageCreate", "MessageResponse", "ConceptResponse",
    # Chat
    "ChatRequest", "ChatResponse", "SourceReference", "YouTubeRecommendation",
    # MindMap
    "MindMapNodeCreate", "MindMapNodeUpdate", "MindMapNodeResponse",
    "MindMapEdgeResponse", "MindMapResponse",
    # Quiz
    "QuizGenerateRequest", "QuizGenerateResponse", "QuizQuestionResponse",
    "QuizSubmitRequest", "QuizResultResponse", "QuizAttemptResponse",
    # Progress
    "SubjectProgressResponse", "OverallProgressResponse", "DashboardDataResponse",
    # Document
    "DocumentUploadResponse", "DocumentResponse", "DocumentListResponse",
    "ProcessingStatusResponse",
]
