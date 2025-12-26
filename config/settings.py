"""
Centralized configuration management using Pydantic settings.
Loads from environment variables with validation.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and type safety"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============================================================================
    # OpenAI Configuration
    # ============================================================================
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # Model selection
    openai_model_classification: str = Field(
        default="gpt-4o",
        description="Model for document classification"
    )
    openai_model_doc_extraction: str = Field(
        default="gpt-4o",
        description="Model for document-level metadata"
    )
    openai_model_chunk_extraction: str = Field(
        default="gpt-4o-mini",
        description="Model for chunk-level metadata (cost optimized)"
    )
    openai_model_query: str = Field(
        default="gpt-4o",
        description="Model for query understanding"
    )
    openai_model_generation: str = Field(
        default="gpt-4o",
        description="Model for answer generation"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model"
    )
    
    # LLM parameters
    llm_temperature_extraction: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for extraction tasks (low = deterministic)"
    )
    llm_temperature_generation: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperature for generation tasks"
    )
    llm_max_tokens_extraction: int = Field(
        default=500,
        gt=0,
        description="Max tokens for extraction"
    )
    llm_max_tokens_generation: int = Field(
        default=1000,
        gt=0,
        description="Max tokens for generation"
    )
    
    # ============================================================================
    # Chunking Configuration
    # ============================================================================
    chunk_size: int = Field(
        default=500,
        gt=0,
        description="Target chunk size in tokens"
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        description="Overlap between chunks in tokens"
    )
    chunk_min_size: int = Field(
        default=100,
        gt=0,
        description="Minimum chunk size to keep"
    )
    
    @field_validator("chunk_overlap", mode="after")
    @classmethod
    def validate_overlap(cls, v: int) -> int:
        """Ensure overlap is less than chunk size"""
        # Note: chunk_size might not be set yet during validation
        # This will be checked at runtime if needed
        return v
    
    # ============================================================================
    # Retrieval Configuration
    # ============================================================================
    top_k_retrieval: int = Field(
        default=5,
        gt=0,
        le=50,
        description="Number of chunks to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval"
    )
    
    # ============================================================================
    # Chroma DB Configuration
    # ============================================================================
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma_db"),
        description="Chroma persistence directory"
    )
    chroma_collection_name: str = Field(
        default="company_docs",
        description="Chroma collection name"
    )
    
    # ============================================================================
    # Paths
    # ============================================================================
    prompts_dir: Path = Field(
        default=Path("./prompts"),
        description="Directory containing markdown prompts"
    )
    data_dir: Path = Field(
        default=Path("./data"),
        description="Base data directory"
    )
    raw_docs_dir: Path = Field(
        default=Path("./data/raw"),
        description="Directory for raw PDF documents"
    )
    
    # ============================================================================
    # Logging
    # ============================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["json", "console"] = Field(
        default="json",
        description="Log output format"
    )
    
    # ============================================================================
    # Feature Flags
    # ============================================================================
    enable_chunk_metadata: bool = Field(
        default=True,
        description="Enable chunk-level metadata extraction"
    )
    enable_reranking: bool = Field(
        default=False,
        description="Enable LLM-based reranking of results"
    )
    enable_query_rewriting: bool = Field(
        default=True,
        description="Enable query reformulation"
    )
    
    # ============================================================================
    # Performance
    # ============================================================================
    max_concurrent_requests: int = Field(
        default=5,
        gt=0,
        description="Max concurrent API requests"
    )
    request_timeout: int = Field(
        default=30,
        gt=0,
        description="Request timeout in seconds"
    )
    retry_max_attempts: int = Field(
        default=3,
        gt=0,
        description="Max retry attempts for failed requests"
    )
    retry_wait_seconds: float = Field(
        default=2.0,
        gt=0,
        description="Wait time between retries"
    )
    
    # ============================================================================
    # Computed Properties
    # ============================================================================
    
    @property
    def processed_docs_dir(self) -> Path:
        """Directory for processed documents"""
        return self.data_dir / "processed"
    
    @property
    def logs_dir(self) -> Path:
        """Directory for logs"""
        return self.data_dir / "logs"
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        dirs = [
            self.data_dir,
            self.raw_docs_dir,
            self.processed_docs_dir,
            self.chroma_persist_dir,
            self.logs_dir,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def validate_settings(self) -> None:
        """Runtime validation of interdependent settings"""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Prompts directory not found: {self.prompts_dir}"
            )
    
    def model_dump_safe(self) -> dict:
        """Dump settings excluding sensitive data"""
        data = self.model_dump()
        data["openai_api_key"] = "***REDACTED***"
        return data


# ============================================================================
# Global Settings Instance
# ============================================================================

# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
        _settings.validate_settings()
    return _settings


# Convenience function for direct import
settings = get_settings()