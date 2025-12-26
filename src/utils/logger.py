"""
Structured logging configuration using structlog.
Provides consistent logging across the application with context.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from config.settings import settings


def setup_logging() -> None:
    """
    Configure structlog for the application.
    
    Uses JSON format for production, console format for development.
    Includes timestamps, log levels, and contextual information.
    """
    
    # Determine processors based on log format
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.log_format == "json":
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Human-readable console output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__ of the module)
        
    Returns:
        Configured structlog logger
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("processing_document", doc_id="123", page_count=5)
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding temporary context to logs.
    
    Example:
        >>> with LogContext(document_id="doc_123", user="admin"):
        ...     logger.info("processing_started")
        # Output includes document_id and user in all logs within context
    """
    
    def __init__(self, **kwargs: Any) -> None:
        self.context = kwargs
        self.token: Any = None
    
    def __enter__(self) -> "LogContext":
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        structlog.contextvars.unbind_contextvars(*self.context.keys())


# Initialize logging on module import
setup_logging()

# Convenience: pre-configured logger for direct import
logger = get_logger("rag_metadata_poc")