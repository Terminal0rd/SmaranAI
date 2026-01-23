"""
Text chunking utilities for RAG
"""
from typing import List


def chunk_text(
    text: str, 
    chunk_size: int = 500, 
    overlap: int = 100
) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: The text to chunk
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or len(text) == 0:
        return []
    
    # Clean the text
    text = text.strip()
    
    # If text is smaller than chunk size, return as single chunk
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # If we're not at the end, try to break at a sentence or paragraph
        if end < len(text):
            # Look for sentence ending within last 100 chars
            search_start = max(end - 100, start)
            search_text = text[search_start:end]
            
            # Try to find a good break point (sentence end)
            for delimiter in ['. ', '.\n', '? ', '?\n', '! ', '!\n', '\n\n']:
                last_pos = search_text.rfind(delimiter)
                if last_pos != -1:
                    end = search_start + last_pos + len(delimiter)
                    break
        else:
            end = len(text)
        
        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        
        # Ensure we make progress
        if start >= len(text):
            break
    
    return chunks


def chunk_by_paragraphs(
    text: str,
    max_chunk_size: int = 1000,
    min_chunk_size: int = 100
) -> List[str]:
    """
    Split text by paragraphs, combining small ones
    
    Args:
        text: The text to chunk
        max_chunk_size: Maximum size of a chunk
        min_chunk_size: Minimum size to keep a chunk
        
    Returns:
        List of paragraph-based chunks
    """
    if not text:
        return []
    
    # Split by double newline (paragraphs)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If adding this paragraph would exceed max size
        if len(current_chunk) + len(para) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    # Add remaining chunk
    if current_chunk and len(current_chunk) >= min_chunk_size:
        chunks.append(current_chunk.strip())
    
    return chunks
