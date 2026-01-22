"""
Chunk debugging system - saves all chunks to JSON BEFORE embedding.

This allows inspection of chunking quality without querying the vector DB.
Critical for debugging retrieval issues and verifying chunk content.

Integration:
    In src/orchestration/nodes.py - chunk_document_node():
    
    from src.ingestion.chunk_debugger import get_chunk_debugger
    
    def chunk_document_node(state: GraphState) -> GraphState:
        # ... chunk document ...
        chunks = chunk_document(...)
        
        # ⭐ SAVE CHUNKS TO DEBUG OUTPUT
        debugger = get_chunk_debugger()
        
        # Save raw document first
        debugger.save_raw_document(
            document_id=state["document_id"],
            document_text=state["raw_text"],
            document_name=state.get("filename", "unknown"),
            metadata=state.get("doc_metadata", {})
        )
        
        # Save each chunk
        for chunk in chunks:
            debugger.save_chunk(
                chunk=chunk,
                document_id=state["document_id"],
                document_name=state.get("filename", "unknown"),
                chunk_config={
                    "chunk_size": 500,
                    "overlap": 100
                }
            )
        
        state["chunks"] = chunks
        return state
"""

from pathlib import Path
import json
from datetime import datetime
import uuid
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChunkDebugger:
    """
    Saves document chunks to JSON files for debugging.
    
    Directory structure:
        data/debug_chunks/
            raw/          - Original documents
            chunked/      - Individual chunk JSONs (BEFORE embedding)
            rejected/     - Rejected/failed chunks
    
    Features:
    - Timestamped filenames for tracking
    - Full chunk metadata + text
    - Embedding status tracking
    - Easy manual inspection
    """
    
    def __init__(self, base_path: Path | None = None):
        """
        Initialize chunk debugger.
        
        Args:
            base_path: Base directory for debug output
                      (default: ./data/debug_chunks)
        """
        self.base_path = base_path or Path("data/debug_chunks")
        self._ensure_directories()
        
        logger.info(
            "chunk_debugger_initialized",
            base_path=str(self.base_path)
        )
    
    def _ensure_directories(self) -> None:
        """Create debug directory structure if it doesn't exist"""
        directories = [
            self.base_path / "raw",
            self.base_path / "chunked",
            self.base_path / "rejected",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.debug(
            "debug_directories_created",
            directories=[str(d) for d in directories]
        )
    
    def save_raw_document(
        self,
        document_id: str,
        document_text: str,
        document_name: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Save raw document before chunking.
        
        Args:
            document_id: Unique document identifier
            document_text: Full document text
            document_name: Original filename
            metadata: Optional document metadata
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{document_id}_{timestamp}_raw.json"
        
        output = {
            "document_id": document_id,
            "document_name": document_name,
            "text_length": len(document_text),
            "word_count": len(document_text.split()),
            "text": document_text,
            "metadata": metadata or {},
            "saved_at": datetime.now().isoformat(),
        }
        
        path = self.base_path / "raw" / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(
            "raw_document_saved",
            document_id=document_id,
            path=str(path),
            size_chars=len(document_text)
        )
        
        return path
    
    def save_chunk(
        self,
        chunk: dict[str, Any],
        document_id: str,
        document_name: str = "unknown",
        source_type: str = "pdf",
        chunk_strategy: str = "simple_fixed",
        chunk_config: dict[str, Any] | None = None,
        embedding_status: str = "pending",
    ) -> str:
        """
        Save individual chunk to JSON BEFORE embedding.
        
        Args:
            chunk: Chunk dictionary with 'text', 'chunk_number', 'metadata'
            document_id: Parent document ID
            document_name: Original document filename
            source_type: Document source (pdf, txt, etc.)
            chunk_strategy: Chunking strategy used
            chunk_config: Chunking configuration (size, overlap)
            embedding_status: Status (pending, embedded, failed)
            
        Returns:
            Unique chunk ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chunk_id = str(uuid.uuid4())
        chunk_number = chunk.get("chunk_number", 0)
        
        filename = f"{document_id}_chunk{chunk_number:04d}_{timestamp}.json"
        
        # Default chunk config
        if chunk_config is None:
            chunk_config = {
                "chunk_size": 500,
                "overlap": 100,
            }
        
        output = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "document_name": document_name,
            "source_type": source_type,
            "chunk_index": chunk_number,
            "chunk_strategy": chunk_strategy,
            
            # Chunk content
            "text": chunk.get("text", ""),
            "text_length": len(chunk.get("text", "")),
            "word_count": len(chunk.get("text", "").split()),
            
            # Metadata
            "metadata": chunk.get("metadata", {}),
            
            # Chunk-specific metadata (if present)
            "chunk_metadata": chunk.get("chunk_metadata", {}),
            
            # Chunking info
            "start_char": chunk.get("start_char", 0),
            "end_char": chunk.get("end_char", 0),
            "chunk_config": chunk_config,
            
            # Status
            "embedding_status": embedding_status,
            "created_at": datetime.now().isoformat(),
        }
        
        path = self.base_path / "chunked" / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.debug(
            "chunk_saved",
            document_id=document_id,
            chunk_number=chunk_number,
            chunk_id=chunk_id,
            path=str(path)
        )
        
        return chunk_id
    
    def save_rejected_chunk(
        self,
        chunk: dict[str, Any],
        document_id: str,
        reason: str,
        error: str | None = None,
    ) -> str:
        """
        Save rejected/failed chunk for debugging.
        
        Args:
            chunk: Chunk that failed
            document_id: Parent document ID
            reason: Why chunk was rejected
            error: Optional error message
            
        Returns:
            Unique chunk ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chunk_id = str(uuid.uuid4())
        chunk_number = chunk.get("chunk_number", 0)
        
        filename = f"{document_id}_chunk{chunk_number:04d}_REJECTED_{timestamp}.json"
        
        output = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "chunk_index": chunk_number,
            "rejection_reason": reason,
            "error": error,
            "chunk_data": chunk,
            "rejected_at": datetime.now().isoformat(),
        }
        
        path = self.base_path / "rejected" / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.warning(
            "chunk_rejected",
            document_id=document_id,
            chunk_number=chunk_number,
            reason=reason,
            error=error
        )
        
        return chunk_id
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about saved chunks.
        
        Returns:
            Dictionary with counts of raw/chunked/rejected files
        """
        stats = {
            "raw_documents": len(list((self.base_path / "raw").glob("*.json"))),
            "chunked_files": len(list((self.base_path / "chunked").glob("*.json"))),
            "rejected_files": len(list((self.base_path / "rejected").glob("*.json"))),
            "base_path": str(self.base_path),
        }
        
        return stats


# ============================================================================
# Global Singleton
# ============================================================================

_debugger: ChunkDebugger | None = None


def get_chunk_debugger() -> ChunkDebugger:
    """
    Get or create the global chunk debugger instance.
    
    Returns:
        Singleton ChunkDebugger instance
    """
    global _debugger
    if _debugger is None:
        _debugger = ChunkDebugger()
    return _debugger