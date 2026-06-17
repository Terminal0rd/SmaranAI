"""
SmaranAI Backend Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./smaranai.db"
    
    # JWT
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # LLM Provider: "groq" for Groq cloud API, "ollama" for local Ollama
    llm_provider: str = "groq"
    
    # Groq API (fast cloud LLM)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Ollama (local LLM - fallback)
    llm_server_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    llm_max_tokens: int = 350
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # File Upload
    max_upload_size_mb: int = 500  # Allow large PDF uploads
    upload_dir: str = "storage/uploads"
    
    # Vector Store (GLOBAL - shared across all users)
    vector_store_path: str = "storage/vectors.pkl"
    
    # Voice Tutor Mode (Text-to-Speech)
    enable_voice_tutor: bool = False  # Set to True to enable audio generation
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
