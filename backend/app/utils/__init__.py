"""
Utilities for SmaranAI
"""
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    get_current_user,
    oauth2_scheme
)
from app.utils.pdf_parser import (
    extract_text_from_pdf,
    validate_pdf,
    get_pdf_page_count
)
from app.utils.text_chunker import (
    chunk_text,
    chunk_by_paragraphs
)

__all__ = [
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "oauth2_scheme",
    # PDF
    "extract_text_from_pdf",
    "validate_pdf",
    "get_pdf_page_count",
    # Chunking
    "chunk_text",
    "chunk_by_paragraphs",
]
