"""
LangGraph state schema for metadata extraction pipeline.
Defines the state that flows through the extraction graph.
"""

from typing import Any, TypedDict

from typing_extensions import NotRequired


class DocumentChunk(TypedDict):
    """
    Represents a single document chunk.
    
    Attributes:
        text: Chunk text content
        chunk_number: Sequential number within document
        start_char: Starting character position in document
        end_char: Ending character position in document
        metadata: Document-level metadata (inherited)
        chunk_metadata: Chunk-specific metadata (optional)
    """
    text: str
    chunk_number: int
    start_char: int
    end_char: int
    metadata: dict[str, Any]
    chunk_metadata: NotRequired[dict[str, Any]]


class GraphState(TypedDict):
    """
    State that flows through the LangGraph metadata extraction pipeline.
    
    This state is passed between nodes and updated at each step.
    """
    
    # ========================================================================
    # Input (Set at start)
    # ========================================================================
    
    document_id: str
    """Unique identifier for this document"""
    
    raw_text: str
    """Original document text"""
    
    filename: NotRequired[str]
    """Original filename (if available)"""
    
    # ========================================================================
    # Classification Stage
    # ========================================================================
    
    classification: NotRequired[dict[str, Any]]
    """
    Document classification result:
    - complexity: simple|structured|complex
    - document_type: HR Policy|Technical Manual|etc.
    - requires_deep_analysis: bool
    - confidence: float
    - reasoning: str
    """
    
    extraction_strategy: NotRequired[str]
    """Extraction strategy: fast|template|deep"""
    
    # ========================================================================
    # Document Metadata Stage
    # ========================================================================
    
    doc_metadata: NotRequired[dict[str, Any]]
    """
    Extracted document-level metadata:
    - document_type
    - department
    - authority_level
    - topics
    - intended_audience
    - effective_date
    - version
    - document_summary
    - etc.
    """
    
    # ========================================================================
    # Chunking Stage
    # ========================================================================
    
    chunks: NotRequired[list[DocumentChunk]]
    """List of document chunks with metadata"""
    
    # ========================================================================
    # Chunk Metadata Stage (Optional)
    # ========================================================================
    
    enriched_chunks: NotRequired[list[DocumentChunk]]
    """Chunks with chunk-level metadata extracted"""
    
    # ========================================================================
    # Validation Stage
    # ========================================================================
    
    validation_errors: NotRequired[list[str]]
    """List of validation errors"""
    
    validation_warnings: NotRequired[list[str]]
    """List of validation warnings"""
    
    is_valid: NotRequired[bool]
    """Whether metadata passed validation"""
    
    # ========================================================================
    # Status and Errors
    # ========================================================================
    
    status: str
    """
    Current pipeline status:
    - pending: Not started
    - classifying: Classification in progress
    - extracting_metadata: Document metadata extraction
    - chunking: Splitting document
    - extracting_chunks: Chunk metadata extraction
    - validating: Validation in progress
    - completed: Successfully completed
    - failed: Pipeline failed
    """
    
    error: NotRequired[str]
    """Error message if status is 'failed'"""
    
    error_stage: NotRequired[str]
    """Which stage failed"""
    
    # ========================================================================
    # Metadata
    # ========================================================================
    
    processing_time: NotRequired[float]
    """Total processing time in seconds"""
    
    tokens_used: NotRequired[int]
    """Total tokens consumed by LLM calls"""
    
    estimated_cost: NotRequired[float]
    """Estimated cost in USD"""


class PipelineConfig(TypedDict, total=False):
    """
    Configuration for the extraction pipeline.
    
    Can be passed when creating the graph to customize behavior.
    """
    
    enable_chunk_metadata: bool
    """Whether to extract chunk-level metadata (default: True for complex docs)"""
    
    chunk_size: int
    """Target chunk size in tokens (default: from settings)"""
    
    chunk_overlap: int
    """Overlap between chunks in tokens (default: from settings)"""
    
    strict_validation: bool
    """Whether to fail on validation errors (default: True)"""
    
    preview_length: int
    """Length of document preview for classification (default: 2000)"""
    
    max_retries: int
    """Maximum retries for failed LLM calls (default: 3)"""


# ========================================================================
# Helper Functions
# ========================================================================

def create_initial_state(
    document_id: str,
    raw_text: str,
    filename: str | None = None,
) -> GraphState:
    """
    Create initial graph state for a document.
    
    Args:
        document_id: Unique document identifier
        raw_text: Document text content
        filename: Original filename (optional)
        
    Returns:
        Initial GraphState
    """
    state: GraphState = {
        "document_id": document_id,
        "raw_text": raw_text,
        "status": "pending",
    }
    
    if filename:
        state["filename"] = filename
    
    return state


def is_state_valid(state: GraphState) -> bool:
    """
    Check if state has all required fields for current stage.
    
    Args:
        state: Current graph state
        
    Returns:
        True if state is valid
    """
    # Must always have these
    if not all(key in state for key in ["document_id", "raw_text", "status"]):
        return False
    
    # Stage-specific validation
    status = state["status"]
    
    if status in ["extracting_metadata", "chunking", "extracting_chunks", "validating", "completed"]:
        if "classification" not in state:
            return False
    
    if status in ["chunking", "extracting_chunks", "validating", "completed"]:
        if "doc_metadata" not in state:
            return False
    
    if status in ["extracting_chunks", "validating", "completed"]:
        if "chunks" not in state:
            return False
    
    return True


def get_state_summary(state: GraphState) -> dict[str, Any]:
    """
    Get a summary of the current state for logging/debugging.
    
    Args:
        state: Current graph state
        
    Returns:
        Summary dictionary
    """
    summary: dict[str, Any] = {
        "document_id": state["document_id"],
        "status": state["status"],
        "text_length": len(state["raw_text"]),
    }
    
    if "filename" in state:
        summary["filename"] = state["filename"]
    
    if "classification" in state:
        summary["classification"] = {
            "type": state["classification"].get("document_type"),
            "complexity": state["classification"].get("complexity"),
            "confidence": state["classification"].get("confidence"),
        }
    
    if "doc_metadata" in state:
        summary["metadata_fields"] = len(state["doc_metadata"])
    
    if "chunks" in state:
        summary["chunk_count"] = len(state["chunks"])
    
    if "validation_errors" in state:
        summary["validation_errors"] = len(state["validation_errors"])
    
    if "error" in state:
        summary["error"] = state["error"]
        summary["error_stage"] = state.get("error_stage")
    
    return summary


def mark_as_failed(
    state: GraphState,
    error: str,
    stage: str,
) -> GraphState:
    """
    Mark state as failed with error information.
    
    Args:
        state: Current state
        error: Error message
        stage: Stage where failure occurred
        
    Returns:
        Updated state
    """
    state["status"] = "failed"
    state["error"] = error
    state["error_stage"] = stage
    return state


def mark_as_completed(state: GraphState) -> GraphState:
    """
    Mark state as successfully completed.
    
    Args:
        state: Current state
        
    Returns:
        Updated state
    """
    state["status"] = "completed"
    return state