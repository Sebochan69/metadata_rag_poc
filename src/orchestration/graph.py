"""
LangGraph state machine for metadata extraction pipeline.
Orchestrates the entire extraction workflow.
"""

import time
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.orchestration.nodes import (
    chunk_document_node,
    classify_document_node,
    extract_chunk_metadata_node,
    extract_doc_metadata_node,
    handle_error_node,
    is_pipeline_successful,
    should_extract_chunk_metadata,
    validate_metadata_node,
)
from src.orchestration.state import GraphState, create_initial_state, get_state_summary
from src.utils.logger import LogContext, get_logger

logger = get_logger(__name__)


class MetadataExtractionPipeline:
    """
    LangGraph-based pipeline for document metadata extraction.
    
    Pipeline stages:
    1. Classification - Determine document type and complexity
    2. Document Metadata - Extract document-level metadata
    3. Chunking - Split document into chunks
    4. Chunk Metadata (conditional) - Extract chunk-level metadata if needed
    5. Validation - Validate all metadata
    """
    
    def __init__(self) -> None:
        self.graph = self._build_graph()
        logger.info("metadata_extraction_pipeline_initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.
        
        Graph structure:
        START → classify → extract_doc_metadata → chunk → [extract_chunks?] → validate → END
                    ↓ (if failed)        ↓ (if failed)   ↓ (if failed)
                handle_error ←───────────┴────────────────┴───────────→ END
        """
        # Create graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("classify", classify_document_node)
        workflow.add_node("extract_doc_metadata", extract_doc_metadata_node)
        workflow.add_node("chunk", chunk_document_node)
        workflow.add_node("extract_chunks", extract_chunk_metadata_node)
        workflow.add_node("validate", validate_metadata_node)
        workflow.add_node("handle_error", handle_error_node)
        
        # Add edges with failure handling
        workflow.add_edge(START, "classify")
        
        # Check for failure after each step
        workflow.add_conditional_edges(
            "classify",
            lambda state: "failed" if state["status"] == "failed" else "continue",
            {
                "continue": "extract_doc_metadata",
                "failed": "handle_error",
            },
        )
        
        workflow.add_conditional_edges(
            "extract_doc_metadata",
            lambda state: "failed" if state["status"] == "failed" else "continue",
            {
                "continue": "chunk",
                "failed": "handle_error",
            },
        )
        
        workflow.add_conditional_edges(
            "chunk",
            lambda state: "failed" if state["status"] == "failed" else should_extract_chunk_metadata(state),
            {
                "extract_chunks": "extract_chunks",
                "validate": "validate",
                "failed": "handle_error",
            },
        )
        
        workflow.add_edge("extract_chunks", "validate")
        workflow.add_edge("validate", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def run(
        self,
        document_id: str,
        document_text: str,
        filename: str | None = None,
    ) -> GraphState:
        """
        Run the extraction pipeline on a document.
        
        Args:
            document_id: Unique document identifier
            document_text: Full document text
            filename: Original filename (optional)
            
        Returns:
            Final GraphState with extracted metadata
        """
        with LogContext(document_id=document_id):
            logger.info(
                "pipeline_started",
                filename=filename,
                text_length=len(document_text),
            )
            
            start_time = time.time()
            
            # Create initial state
            initial_state = create_initial_state(
                document_id=document_id,
                raw_text=document_text,
                filename=filename,
            )
            
            try:
                # Run the graph
                final_state = self.graph.invoke(initial_state)
                
                # Add timing info
                processing_time = time.time() - start_time
                final_state["processing_time"] = processing_time
                
                # Get token usage from LLM client
                from src.utils.llm_client import get_llm_client
                client = get_llm_client()
                stats = client.get_usage_stats()
                final_state["tokens_used"] = stats["total_tokens"]
                final_state["estimated_cost"] = float(stats["total_cost"].replace("$", ""))
                
                # Log completion
                summary = get_state_summary(final_state)
                logger.info(
                    "pipeline_completed",
                    status=final_state["status"],
                    processing_time=f"{processing_time:.2f}s",
                    tokens_used=stats["total_tokens"],
                    cost=stats["total_cost"],
                    summary=summary,
                )
                
                return final_state
                
            except Exception as e:
                logger.error(
                    "pipeline_exception",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                
                # Mark as failed
                initial_state["status"] = "failed"
                initial_state["error"] = str(e)
                initial_state["error_stage"] = "pipeline_execution"
                initial_state["processing_time"] = time.time() - start_time
                
                return initial_state
    
    async def arun(
        self,
        document_id: str,
        document_text: str,
        filename: str | None = None,
    ) -> GraphState:
        """
        Async version of run (for future use).
        
        Currently just wraps synchronous run.
        """
        return self.run(document_id, document_text, filename)
    
    def visualize(self, output_path: str = "pipeline_graph.png") -> None:
        """
        Visualize the pipeline graph (requires graphviz).
        
        Args:
            output_path: Path to save visualization
        """
        try:
            from IPython.display import Image, display
            
            # Get graph visualization
            graph_image = self.graph.get_graph().draw_mermaid_png()
            
            # Save or display
            with open(output_path, "wb") as f:
                f.write(graph_image)
            
            logger.info("pipeline_visualization_saved", path=output_path)
            
        except ImportError:
            logger.warning(
                "pipeline_visualization_unavailable",
                reason="IPython or graphviz not installed",
            )
        except Exception as e:
            logger.error(
                "pipeline_visualization_failed",
                error=str(e),
            )


# ============================================================================
# Global pipeline instance
# ============================================================================

_pipeline: MetadataExtractionPipeline | None = None


def get_pipeline() -> MetadataExtractionPipeline:
    """
    Get or create the global pipeline instance.
    
    Returns:
        Singleton MetadataExtractionPipeline instance
    """
    global _pipeline
    if _pipeline is None:
        _pipeline = MetadataExtractionPipeline()
    return _pipeline


def run_extraction(
    document_id: str,
    document_text: str,
    filename: str | None = None,
) -> GraphState:
    """
    Convenience function to run extraction pipeline.
    
    Args:
        document_id: Unique document identifier
        document_text: Full document text
        filename: Original filename (optional)
        
    Returns:
        Final state with extracted metadata
    """
    pipeline = get_pipeline()
    return pipeline.run(document_id, document_text, filename)