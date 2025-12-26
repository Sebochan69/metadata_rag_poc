"""
Document chunking with semantic awareness.
Splits documents into overlapping chunks for vector storage.
"""

from typing import Any

import tiktoken

from config.settings import settings
from src.orchestration.state import DocumentChunk
from src.utils.logger import get_logger

logger = get_logger(__name__)


def chunk_document(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    document_metadata: dict[str, Any] | None = None,
) -> list[DocumentChunk]:
    """
    Split document into chunks with overlap.
    
    Args:
        text: Document text to chunk
        chunk_size: Target chunk size in tokens (default: from settings)
        chunk_overlap: Overlap between chunks in tokens (default: from settings)
        document_metadata: Metadata to inherit (default: None)
        
    Returns:
        List of DocumentChunk objects
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    logger.info(
        "chunking_started",
        text_length=len(text),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    # Get tokenizer
    encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
    
    # Tokenize text
    tokens = encoding.encode(text)
    
    chunks: list[DocumentChunk] = []
    start_idx = 0
    chunk_num = 0
    
    while start_idx < len(tokens):
        # Calculate end index
        end_idx = start_idx + chunk_size
        
        # Extract chunk tokens
        chunk_tokens = tokens[start_idx:end_idx]
        
        # Decode back to text
        chunk_text = encoding.decode(chunk_tokens)
        
        # Find character positions
        # (approximate - token boundaries don't align perfectly with chars)
        start_char = len(encoding.decode(tokens[:start_idx]))
        end_char = start_char + len(chunk_text)
        
        # Create chunk
        chunk: DocumentChunk = {
            "text": chunk_text,
            "chunk_number": chunk_num,
            "start_char": start_char,
            "end_char": end_char,
            "metadata": document_metadata or {},
        }
        
        chunks.append(chunk)
        
        # Move to next chunk with overlap
        start_idx += chunk_size - chunk_overlap
        chunk_num += 1
    
    logger.info(
        "chunking_completed",
        chunk_count=len(chunks),
        avg_chunk_length=sum(len(c["text"]) for c in chunks) // len(chunks) if chunks else 0,
    )
    
    return chunks