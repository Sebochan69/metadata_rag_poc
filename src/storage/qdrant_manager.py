"""
Qdrant vector store manager.
Handles storage and retrieval of document chunks with metadata.

Qdrant advantages over ChromaDB:
- Native array support for topics/audiences
- Better metadata filtering performance
- Nested object support
- Production-ready scalability
"""

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

from config.settings import settings
from src.orchestration.state import DocumentChunk
from src.storage.embedder import get_embedder
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QdrantManager:
    """
    Manages Qdrant vector store operations.
    
    Features:
    - Stores document chunks with embeddings and metadata
    - Native array support for topics/audiences
    - Metadata-filtered vector search
    - Automatic embedding generation
    """
    
    def __init__(
        self,
        collection_name: str | None = None,
        url: str = "http://localhost:6333",
        api_key: str | None = None,
    ) -> None:
        """
        Initialize Qdrant manager.
        
        Args:
            collection_name: Name of collection (default: from settings)
            url: Qdrant server URL (default: localhost)
            api_key: API key for Qdrant Cloud (optional)
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=url,
            api_key=api_key,
        )
        
        # Get embedder
        self.embedder = get_embedder()
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
        
        logger.info(
            "qdrant_manager_initialized",
            collection=self.collection_name,
            url=url,
        )
    
    def _ensure_collection_exists(self) -> None:
        """Create collection if it doesn't exist"""
        
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            logger.info("creating_qdrant_collection", collection=self.collection_name)
            
            # Create collection with vector config
            # OpenAI text-embedding-3-small produces 1536-dimensional vectors
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI embedding dimension
                    distance=Distance.COSINE,
                ),
            )
            
            logger.info("qdrant_collection_created")
        else:
            logger.info("qdrant_collection_exists")
    
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
        
        # Prepare data for Qdrant
        points = []
        texts = []
        
        for chunk in chunks:
            texts.append(chunk["text"])
        
        # Generate embeddings
        logger.info("generating_embeddings", chunk_count=len(texts))
        embeddings = self.embedder.embed_texts(texts)
        
        # Create points
        for i, chunk in enumerate(chunks):
            # Generate unique ID - use hash for UUID-like ID
            import hashlib
            point_id_str = f"{document_id}_chunk_{chunk['chunk_number']}"
            point_id = int(hashlib.md5(point_id_str.encode()).hexdigest()[:8], 16)  # Convert to int
            
            # Prepare metadata (Qdrant supports native arrays!)
            payload = self._prepare_payload(chunk, document_id)
            
            # Create point
            point = PointStruct(
                id=point_id,  # Now an integer
                vector=embeddings[i],
                payload=payload,
            )
            
            points.append(point)
        
        # Upsert to Qdrant
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            
            logger.info(
                "chunks_added_successfully",
                document_id=document_id,
                chunk_count=len(chunks),
            )
            
        except Exception as e:
            logger.error(
                "failed_to_add_chunks",
                document_id=document_id,
                error=str(e),
            )
            raise
    
    def _prepare_payload(
        self,
        chunk: DocumentChunk,
        document_id: str,
    ) -> dict[str, Any]:
        """
        Prepare payload for Qdrant storage.
        
        Qdrant supports:
        - Native arrays (no need to stringify!)
        - Nested objects
        - All primitive types
        """
        metadata = chunk["metadata"].copy()
        
        # Add chunk-specific fields
        payload = {
            "document_id": document_id,
            "chunk_number": chunk["chunk_number"],
            "start_char": chunk["start_char"],
            "end_char": chunk["end_char"],
            "text": chunk["text"],  # Store text in payload
            
            # Document metadata (with native arrays!)
            "domain": metadata.get("domain"),
            "document_type": metadata.get("document_type"),
            "department": metadata.get("department"),
            "authority_level": metadata.get("authority_level"),
            "topics": metadata.get("topics", []),  # Native array!
            "intended_audience": metadata.get("intended_audience", []),  # Native array!
            "effective_date": metadata.get("effective_date"),
            "version": metadata.get("version"),
            "compliance_related": metadata.get("compliance_related", False),
            "requires_acknowledgment": metadata.get("requires_acknowledgment", False),
        }
        
        # Add chunk metadata if present
        if "chunk_metadata" in chunk:
            for key, value in chunk["chunk_metadata"].items():
                payload[f"chunk_{key}"] = value
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        return payload
    
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
            where: Metadata filters (Qdrant filter format)
            
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
            filters=where is not None,
        )
        
        # Generate query embedding
        query_embedding = self.embedder.embed_single(query)
        
        # Build Qdrant filter
        qdrant_filter = self._build_qdrant_filter(where) if where else None
        
        # Search - use the correct method name
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=n_results,
                query_filter=qdrant_filter,
            )
            
            # Format results (similar to ChromaDB format for compatibility)
            ids = []
            documents = []
            metadatas = []
            distances = []
            
            for result in results.points:
                ids.append(str(result.id))
                documents.append(result.payload.get("text", ""))
                
                # Extract metadata (exclude text)
                metadata = {k: v for k, v in result.payload.items() if k != "text"}
                metadatas.append(metadata)
                
                # Qdrant returns score (higher is better)
                # Convert to distance (lower is better) for compatibility
                distances.append(1.0 - result.score)
            
            logger.info(
                "search_completed",
                results_found=len(ids),
            )
            
            return {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "distances": distances,
            }
            
        except Exception as e:
            logger.error(
                "search_failed",
                error=str(e),
            )
            raise
    
    def _build_qdrant_filter(self, where: dict[str, Any]) -> Filter:
        """
        Build Qdrant filter from ChromaDB-style where clause.
        
        Converts from ChromaDB format to Qdrant filter format.
        
        Args:
            where: ChromaDB-style where clause
            
        Returns:
            Qdrant Filter object
        """
        conditions = []
        
        # Handle direct field matches
        if "domain" in where:
            if isinstance(where["domain"], dict) and "$in" in where["domain"]:
                # Multiple domains: domain in [...]
                conditions.append(
                    FieldCondition(
                        key="domain",
                        match=MatchAny(any=where["domain"]["$in"]),
                    )
                )
            else:
                # Single domain: domain = "Medical"
                conditions.append(
                    FieldCondition(
                        key="domain",
                        match=MatchValue(value=where["domain"]),
                    )
                )
        
        if "document_type" in where:
            if isinstance(where["document_type"], dict) and "$in" in where["document_type"]:
                conditions.append(
                    FieldCondition(
                        key="document_type",
                        match=MatchAny(any=where["document_type"]["$in"]),
                    )
                )
            else:
                conditions.append(
                    FieldCondition(
                        key="document_type",
                        match=MatchValue(value=where["document_type"]),
                    )
                )
        
        if "department" in where:
            if isinstance(where["department"], dict) and "$in" in where["department"]:
                conditions.append(
                    FieldCondition(
                        key="department",
                        match=MatchAny(any=where["department"]["$in"]),
                    )
                )
            else:
                conditions.append(
                    FieldCondition(
                        key="department",
                        match=MatchValue(value=where["department"]),
                    )
                )
        
        # Handle $and operator
        if "$and" in where:
            for clause in where["$and"]:
                # Recursively build sub-filters
                sub_filter = self._build_qdrant_filter(clause)
                conditions.extend(sub_filter.must)
        
        return Filter(must=conditions)
    
    def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document identifier
        """
        logger.info("deleting_document", document_id=document_id)
        
        try:
            # Delete by filter (document_id field)
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                ),
            )
            
            logger.info("document_deleted", document_id=document_id)
            
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
        info = self.client.get_collection(self.collection_name)
        
        return {
            "collection_name": self.collection_name,
            "total_chunks": info.points_count,
            "vector_size": info.config.params.vectors.size,
        }
    
    def reset_collection(self) -> None:
        """
        Delete all data in the collection.
        
        WARNING: This is destructive and cannot be undone!
        """
        logger.warning("resetting_collection", collection=self.collection_name)
        
        self.client.delete_collection(self.collection_name)
        self._ensure_collection_exists()
        
        logger.info("collection_reset_completed")


# Global manager instance
_manager: QdrantManager | None = None


def get_qdrant_manager() -> QdrantManager:
    """
    Get or create the global Qdrant manager instance.
    
    Returns:
        Singleton QdrantManager instance
    """
    global _manager
    if _manager is None:
        _manager = QdrantManager()
    return _manager