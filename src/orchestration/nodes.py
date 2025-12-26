"""
LangGraph node functions for the metadata extraction pipeline.
Each function represents a step in the extraction workflow.
"""

import time
from typing import Any

from src.ingestion.chunker import chunk_document
from src.metadata.classifier import get_classifier
from src.metadata.doc_extractor import get_doc_extractor
from src.metadata.validator import MetadataValidationError, get_validator
from src.orchestration.state import GraphState, mark_as_failed
from src.utils.logger import LogContext, get_logger

logger = get_logger(__name__)


# ============================================================================
# Node: Classify Document
# ============================================================================

def classify_document_node(state: GraphState) -> GraphState:
    """
    Classify document to determine extraction strategy.
    
    Updates state with:
    - classification: Classification result
    - extraction_strategy: Strategy to use (fast/template/deep)
    """
    with LogContext(document_id=state["document_id"]):
        logger.info("node_classify_started")
        state["status"] = "classifying"
        
        try:
            classifier = get_classifier()
            
            # Classify document
            classification = classifier.classify(
                document_text=state["raw_text"],
                preview_length=2000,  # TODO: Get from config
            )
            
            # Update state
            state["classification"] = classification.to_dict()
            
            # Determine extraction strategy
            strategy = classifier.get_extraction_strategy(classification)
            state["extraction_strategy"] = strategy
            
            logger.info(
                "node_classify_completed",
                document_type=classification.document_type,
                complexity=classification.complexity,
                strategy=strategy,
                confidence=classification.confidence,
            )
            
            state["status"] = "extracting_metadata"
            return state
            
        except Exception as e:
            logger.error("node_classify_failed", error=str(e))
            return mark_as_failed(
                state,
                error=f"Classification failed: {str(e)}",
                stage="classification",
            )


# ============================================================================
# Node: Extract Document Metadata
# ============================================================================

def extract_doc_metadata_node(state: GraphState) -> GraphState:
    """
    Extract document-level metadata using LLM.
    
    Updates state with:
    - doc_metadata: Extracted metadata dictionary
    """
    with LogContext(document_id=state["document_id"]):
        logger.info("node_extract_doc_metadata_started")
        
        try:
            # Debug: print to console
            print(f"DEBUG: state['classification'] type = {type(state['classification'])}")
            print(f"DEBUG: state['classification'] = {state['classification']}")
            
            extractor = get_doc_extractor()
            
            # Reconstruct classification result
            from src.metadata.classifier import ClassificationResult
            
            classification_dict = state["classification"]
            
            print(f"DEBUG: About to create ClassificationResult...")
            classification = ClassificationResult(
                complexity=classification_dict["complexity"],
                document_type=classification_dict["document_type"],
                requires_deep_analysis=classification_dict["requires_deep_analysis"],
                confidence=classification_dict["confidence"],
                reasoning=classification_dict.get("reasoning", ""),
                raw_response=classification_dict,
            )
            
            print(f"DEBUG: ClassificationResult created: {classification}")
            print(f"DEBUG: classification.document_type = {classification.document_type}")
            
            # Extract metadata
            metadata = extractor.extract(
                document_text=state["raw_text"],
                classification=classification,
            )
            
            state["doc_metadata"] = metadata
            
            logger.info(
                "node_extract_doc_metadata_completed",
                metadata_fields=len(metadata),
                topics=metadata.get("topics", []),
            )
            
            state["status"] = "chunking"
            return state
            
        except Exception as e:
            logger.error(
                "node_extract_doc_metadata_failed", 
                error=str(e),
                error_type=type(e).__name__,
            )
            import traceback
            print(f"DEBUG TRACEBACK:\n{traceback.format_exc()}")
            return mark_as_failed(
                state,
                error=f"Document metadata extraction failed: {str(e)}",
                stage="doc_metadata_extraction",
            )


# ============================================================================
# Node: Chunk Document
# ============================================================================

def chunk_document_node(state: GraphState) -> GraphState:
    """
    Split document into chunks with inherited metadata.
    
    Updates state with:
    - chunks: List of document chunks with metadata
    """
    with LogContext(document_id=state["document_id"]):
        logger.info("node_chunk_document_started")
        
        try:
            # Chunk the document
            chunks = chunk_document(
                text=state["raw_text"],
                chunk_size=500,  # TODO: Get from settings
                chunk_overlap=50,
                document_metadata=state["doc_metadata"],
            )
            
            state["chunks"] = chunks
            
            logger.info(
                "node_chunk_document_completed",
                chunk_count=len(chunks),
            )
            
            # Decide next step based on classification
            classification = state["classification"]
            if classification["requires_deep_analysis"]:
                state["status"] = "extracting_chunks"
            else:
                state["status"] = "validating"
            
            return state
            
        except Exception as e:
            logger.error("node_chunk_document_failed", error=str(e))
            return mark_as_failed(
                state,
                error=f"Document chunking failed: {str(e)}",
                stage="chunking",
            )


# ============================================================================
# Node: Extract Chunk Metadata (Optional)
# ============================================================================

def extract_chunk_metadata_node(state: GraphState) -> GraphState:
    """
    Extract chunk-level metadata for each chunk.
    
    Updates state with:
    - enriched_chunks: Chunks with additional chunk-specific metadata
    
    Note: This is a placeholder. Full implementation in Phase 5.
    """
    with LogContext(document_id=state["document_id"]):
        logger.info("node_extract_chunk_metadata_started")
        
        try:
            # TODO: Implement chunk metadata extraction
            # For now, just copy chunks to enriched_chunks
            state["enriched_chunks"] = state["chunks"]
            
            logger.info(
                "node_extract_chunk_metadata_completed",
                chunk_count=len(state["chunks"]),
            )
            
            state["status"] = "validating"
            return state
            
        except Exception as e:
            logger.error("node_extract_chunk_metadata_failed", error=str(e))
            return mark_as_failed(
                state,
                error=f"Chunk metadata extraction failed: {str(e)}",
                stage="chunk_metadata_extraction",
            )


# ============================================================================
# Node: Validate Metadata
# ============================================================================

def validate_metadata_node(state: GraphState) -> GraphState:
    """
    Validate extracted metadata against schema and business rules.
    
    Updates state with:
    - validation_errors: List of validation errors
    - validation_warnings: List of warnings
    - is_valid: Whether validation passed
    """
    with LogContext(document_id=state["document_id"]):
        logger.info("node_validate_metadata_started")
        
        try:
            validator = get_validator()
            
            # Validate document metadata
            try:
                validated_metadata = validator.validate(
                    metadata=state["doc_metadata"],
                    strict=False,  # Don't raise exception, collect errors
                    fix_minor_issues=True,
                )
                
                # Update with fixed metadata
                state["doc_metadata"] = validated_metadata
                
                # Get validation summary
                summary = validator.get_validation_summary(validated_metadata)
                
                state["is_valid"] = summary["is_valid"]
                state["validation_errors"] = summary.get("errors", [])
                
                # Add warnings for low confidence
                warnings = []
                if summary["is_low_confidence"]:
                    warnings.append(
                        "Low confidence classification - manual review recommended"
                    )
                state["validation_warnings"] = warnings
                
                logger.info(
                    "node_validate_metadata_completed",
                    is_valid=summary["is_valid"],
                    error_count=len(summary.get("errors", [])),
                    warning_count=len(warnings),
                )
                
            except MetadataValidationError as e:
                state["is_valid"] = False
                state["validation_errors"] = e.errors
                state["validation_warnings"] = []
                
                logger.warning(
                    "node_validate_metadata_failed",
                    error_count=len(e.errors),
                    errors=e.errors[:3],  # Log first 3
                )
            
            state["status"] = "completed"
            return state
            
        except Exception as e:
            logger.error("node_validate_unexpected_error", error=str(e))
            return mark_as_failed(
                state,
                error=f"Validation failed unexpectedly: {str(e)}",
                stage="validation",
            )


# ============================================================================
# Node: Handle Errors
# ============================================================================

def handle_error_node(state: GraphState) -> GraphState:
    """
    Handle errors from previous nodes.
    
    This node is called when previous nodes fail.
    It logs the error and marks the pipeline as failed.
    """
    with LogContext(document_id=state["document_id"]):
        logger.error(
            "pipeline_failed",
            error=state.get("error", "Unknown error"),
            stage=state.get("error_stage", "Unknown stage"),
        )
        
        # State is already marked as failed by the failing node
        return state


# ============================================================================
# Conditional Edge Functions
# ============================================================================

def should_extract_chunk_metadata(state: GraphState) -> str:
    """
    Determine if chunk metadata extraction is needed.
    
    Returns:
        "extract_chunks" if chunk metadata needed, else "validate"
    """
    classification = state.get("classification", {})
    
    if classification.get("requires_deep_analysis", False):
        return "extract_chunks"
    else:
        return "validate"


def is_pipeline_successful(state: GraphState) -> str:
    """
    Check if pipeline completed successfully.
    
    Returns:
        "success" if completed, "failed" if error
    """
    if state["status"] == "failed":
        return "failed"
    else:
        return "success"