"""
PDF parsing utilities
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text content from a PDF file
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    text = []
    
    try:
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():
                text.append(page_text)
        
        doc.close()
        
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    return "\n\n".join(text)


def validate_pdf(file_path: str) -> bool:
    """
    Validate that a file is a valid PDF
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if valid PDF, False otherwise
    """
    try:
        # Check magic bytes
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False
        
        # Try to open with PyMuPDF
        doc = fitz.open(file_path)
        is_valid = doc.page_count > 0
        doc.close()
        
        return is_valid
        
    except Exception:
        return False


def get_pdf_page_count(file_path: str) -> int:
    """Get the number of pages in a PDF"""
    try:
        doc = fitz.open(file_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0
