"""
PDF loading and text extraction.
"""

from pathlib import Path

import pymupdf  # PyMuPDF

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        FileNotFoundError: If PDF doesn't exist
        Exception: If PDF cannot be read
    """
    pdf_path_obj = Path(pdf_path)
    
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    logger.info(
        "loading_pdf",
        path=pdf_path,
        size_mb=round(pdf_path_obj.stat().st_size / (1024 * 1024), 2),
    )
    
    try:
        doc = pymupdf.open(pdf_path)
        text = ""
        
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            text += page_text
            
            if page_num % 10 == 0:  # Log every 10 pages
                logger.debug(
                    "pdf_pages_processed",
                    pages_done=page_num,
                    total_pages=len(doc),
                )
        
        doc.close()
        
        logger.info(
            "pdf_loaded_successfully",
            path=pdf_path,
            pages=len(doc),
            total_chars=len(text),
            total_words=len(text.split()),
        )
        
        return text
        
    except Exception as e:
        logger.error(
            "pdf_load_failed",
            path=pdf_path,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


def load_text_file(file_path: str) -> str:
    """
    Load a plain text file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        File contents
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info("loading_text_file", path=file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(
            "text_file_loaded",
            path=file_path,
            chars=len(text),
            words=len(text.split()),
        )
        
        return text
        
    except Exception as e:
        logger.error(
            "text_file_load_failed",
            path=file_path,
            error=str(e),
        )
        raise


def load_document(file_path: str) -> str:
    """
    Load a document (auto-detects format).
    
    Args:
        file_path: Path to document
        
    Returns:
        Extracted text
        
    Raises:
        ValueError: If file format is not supported
    """
    file_path_obj = Path(file_path)
    extension = file_path_obj.suffix.lower()
    
    if extension == '.pdf':
        return load_pdf(file_path)
    elif extension in ['.txt', '.md']:
        return load_text_file(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            "Supported formats: .pdf, .txt, .md"
        )