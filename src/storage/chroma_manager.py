"""
ChromaDB vector store manager.
Handles storage and retrieval of document chunks with metadata.
"""

from typing import Any

import chromadb
from chromadb.config import Settings

from config.settings import settings
from src.orchestration.state import DocumentChunk
from src.storage.embedder import get_embedder
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaManager:
    """
    Manages ChromaDB vector store operations.
    
    Features:
    - Stores document chunks with embeddings and metadata
    - Metadata-filtered vector search
    - Automatic embedding generation
    """
    
    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str | None = None,
    ) -> None:
        """
        Initialize ChromaDB manager.
        
        Args:
            collection_name: Name of collection (default: from settings)
            persist_directory: Where to persist data (default: from settings)
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.persist_directory = str(
            persist_directory or settings.chroma_persist_dir
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "RAG document chunks with metadata"},
        )
        
        # Initialize embedder
        self.embedder = get_embedder()
        
        logger.info(
            "chroma_manager_initialized",
            collection=self.collection_name,
            persist_dir=self.persist_directory,
            existing_count=self.collection.count(),
        )
    
    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        document_id: str,
    ) -> None:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of document chunks with metadata
            document_id: Document identifier
        """
        if not chunks:
            logger.warning("add_chunks_called_with_empty_list")
            return
        
        logger.info(
            "adding_chunks_started",
            document_id=document_id,
            chunk_count=len(chunks),
        )
        
        # Prepare data for ChromaDB
        ids = []
        texts = []
        embeddings_list = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Generate unique ID
            chunk_id = f"{document_id}_chunk_{chunk['chunk_number']}"
            ids.append(chunk_id)
            
            # Extract text
            texts.append(chunk["text"])
            
            # Prepare metadata (flatten for Chroma)
            metadata = self._prepare_metadata(chunk, document_id)
            metadatas.append(metadata)
        
        # Generate embeddings
        logger.info("generating_embeddings", chunk_count=len(texts))
        embeddings_list = self.embedder.embed_texts(texts)
        
        # Add to ChromaDB
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings_list,
                metadatas=metadatas,
            )
            
            logger.info(
                "chunks_added_successfully",
                document_id=document_id,
                chunk_count=len(chunks),
                total_in_collection=self.collection.count(),
            )
            
        except Exception as e:
            logger.error(
                "failed_to_add_chunks",
                document_id=document_id,
                error=str(e),
            )
            raise
    
    def _prepare_metadata(
        self,
        chunk: DocumentChunk,
        document_id: str,
    ) -> dict[str, Any]:
        """
        Prepare metadata for ChromaDB storage.
        
        ChromaDB requirements:
        - Only primitive types (str, int, float, bool)
        - No nested structures
        - Arrays become comma-separated strings
        """
        metadata = chunk["metadata"].copy()
        
        # Add chunk-specific fields
        metadata["document_id"] = document_id
        metadata["chunk_number"] = chunk["chunk_number"]
        metadata["start_char"] = chunk["start_char"]
        metadata["end_char"] = chunk["end_char"]
        
        # Add chunk metadata if present
        if "chunk_metadata" in chunk:
            for key, value in chunk["chunk_metadata"].items():
                if not isinstance(value, (list, dict)):
                    metadata[f"chunk_{key}"] = value
        
        # Flatten arrays to comma-separated strings
        for key, value in list(metadata.items()):
            if isinstance(value, list):
                # Convert list to comma-separated string
                metadata[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Skip nested dicts (not supported by Chroma)
                del metadata[key]
            elif value is None:
                # Remove None values
                del metadata[key]
        
        return metadata
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            where: Metadata filters (ChromaDB where clause)
            
        Returns:
            Dictionary with:
                - ids: List of chunk IDs
                - documents: List of chunk texts
                - metadatas: List of metadata dicts
                - distances: List of similarity distances
        """
        logger.info(
            "search_started",
            query_length=len(query),
            n_results=n_results,
            filters=where,
        )
        
        # Generate query embedding
        query_embedding = self.embedder.embed_single(query)
        
        # Search
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            
            logger.info(
                "search_completed",
                results_found=len(results["ids"][0]) if results["ids"] else 0,
            )
            
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
            }
            
        except Exception as e:
            logger.error(
                "search_failed",
                error=str(e),
            )
            raise
    
    def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document identifier
        """
        logger.info("deleting_document", document_id=document_id)
        
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=[],
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(
                    "document_deleted",
                    document_id=document_id,
                    chunks_deleted=len(results["ids"]),
                )
            else:
                logger.warning(
                    "document_not_found",
                    document_id=document_id,
                )
                
        except Exception as e:
            logger.error(
                "delete_document_failed",
                document_id=document_id,
                error=str(e),
            )
            raise
    
    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection stats
        """
        return {
            "collection_name": self.collection_name,
            "total_chunks": self.collection.count(),
            "persist_directory": self.persist_directory,
        }
    
    def reset_collection(self) -> None:
        """
        Delete all data in the collection.
        
        WARNING: This is destructive and cannot be undone!
        """
        logger.warning("resetting_collection", collection=self.collection_name)
        
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "RAG document chunks with metadata"},
        )
        
        logger.info("collection_reset_completed")


# Global manager instance
_manager: ChromaManager | None = None


def get_chroma_manager() -> ChromaManager:
    """
    Get or create the global ChromaDB manager instance.
    
    Returns:
        Singleton ChromaManager instance
    """
    global _manager
    if _manager is None:
        _manager = ChromaManager()
    return _manager