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
    
    # LLM Server (Ollama with Qwen 2.5)
    llm_server_url: str = "http://127.0.0.1:11434"
    llm_max_tokens: int = 600
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # File Upload
    max_upload_size_mb: int = 500  # Allow large PDF uploads
    upload_dir: str = "storage/uploads"
    
    # Vector Store (GLOBAL - shared across all users)
    vector_store_path: str = "storage/vectors.pkl"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
