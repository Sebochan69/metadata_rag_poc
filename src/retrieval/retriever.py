"""
Document retrieval with metadata filtering.
Combines vector similarity search with structured metadata filters.
"""

import json
from typing import Any

from config.settings import settings
from src.metadata.prompt_loader import get_prompt_loader
from src.storage.chroma_manager import get_chroma_manager
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QueryResult:
    """
    Result from a retrieval query.
    
    Attributes:
        query: Original query
        reformulated_query: LLM-optimized query
        intent: Query intent type
        chunks: Retrieved chunks with metadata
        filters_used: Metadata filters applied
        total_results: Number of results found
    """
    
    def __init__(
        self,
        query: str,
        reformulated_query: str,
        intent: str,
        chunks: list[dict[str, Any]],
        filters_used: dict[str, Any],
    ) -> None:
        self.query = query
        self.reformulated_query = reformulated_query
        self.intent = intent
        self.chunks = chunks
        self.filters_used = filters_used
        self.total_results = len(chunks)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "reformulated_query": self.reformulated_query,
            "intent": self.intent,
            "total_results": self.total_results,
            "filters_used": self.filters_used,
            "chunks": self.chunks,
        }


class Retriever:
    """
    Retrieves relevant document chunks using metadata-filtered vector search.
    
    Features:
    - Query understanding with LLM
    - Metadata filter extraction
    - Vector similarity search
    - Results ranking
    """
    
    def __init__(self) -> None:
        self.chroma = get_chroma_manager()
        self.llm_client = get_llm_client()
        self.prompt_loader = get_prompt_loader()
        
        logger.info("retriever_initialized")
    
    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        use_query_understanding: bool = True,
    ) -> QueryResult:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            top_k: Number of results to return (default: from settings)
            use_query_understanding: Whether to use LLM for query analysis
            
        Returns:
            QueryResult with retrieved chunks
        """
        top_k = top_k or settings.top_k_retrieval
        
        logger.info(
            "retrieval_started",
            query=query,
            top_k=top_k,
            use_understanding=use_query_understanding,
        )
        
        if use_query_understanding:
            # Use LLM to understand query and extract filters
            query_analysis = self._understand_query(query)
            
            reformulated_query = query_analysis.get(
                "reformulated_query", query
            )
            intent = query_analysis.get("intent", "factual")
            filters = self._build_filters(query_analysis)
        else:
            # Direct search without query understanding
            reformulated_query = query
            intent = "factual"
            filters = None
        
        # Search ChromaDB
        results = self.chroma.search(
            query=reformulated_query,
            n_results=top_k,
            where=filters,
        )
        
        # Format results
        chunks = self._format_results(results)
        
        logger.info(
            "retrieval_completed",
            original_query=query,
            reformulated=reformulated_query,
            intent=intent,
            results_found=len(chunks),
            filters_used=filters is not None,
        )
        
        return QueryResult(
            query=query,
            reformulated_query=reformulated_query,
            intent=intent,
            chunks=chunks,
            filters_used=filters or {},
        )
    
    def _understand_query(self, query: str) -> dict[str, Any]:
        """
        Use LLM to understand query intent and extract filters.
        
        Args:
            query: User query
            
        Returns:
            Query analysis dictionary
        """
        logger.debug("understanding_query", query=query)
        
        # Load and format prompt
        prompt = self.prompt_loader.get_prompt_text(
            "query_understanding",
            query=query,
        )
        
        # Get analysis from LLM
        try:
            analysis = self.llm_client.complete_json(
                prompt=prompt,
                temperature=0.2,  # Some creativity for reformulation
                max_tokens=300,
            )
            
            logger.debug(
                "query_understood",
                intent=analysis.get("intent"),
                confidence=analysis.get("confidence"),
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error("query_understanding_json_failed", error=str(e))
            # Fallback to original query
            return {
                "intent": "factual",
                "query_type": "simple_lookup",
                "required_filters": {},
                "optional_filters": {},
                "reformulated_query": query,
                "confidence": 0.5,
            }
        except Exception as e:
            logger.error("query_understanding_failed", error=str(e))
            # Fallback to original query
            return {
                "intent": "factual",
                "query_type": "simple_lookup",
                "required_filters": {},
                "optional_filters": {},
                "reformulated_query": query,
                "confidence": 0.5,
            }
    
    def _build_filters(self, query_analysis: dict[str, Any]) -> dict[str, Any] | None:
        """
        Build ChromaDB where clause from query analysis.
        
        Args:
            query_analysis: Analysis from query understanding
            
        Returns:
            ChromaDB where clause or None
        """
        required_filters = query_analysis.get("required_filters", {})
        
        if not required_filters:
            return None
        
        where_clauses = []
        
        # Handle document_type
        if "document_type" in required_filters and required_filters["document_type"]:
            doc_types = required_filters["document_type"]
            if len(doc_types) == 1:
                where_clauses.append({"document_type": doc_types[0]})
            else:
                # Multiple types - need OR logic (ChromaDB $in operator)
                where_clauses.append({"document_type": {"$in": doc_types}})
        
        # Handle department
        if "department" in required_filters and required_filters["department"]:
            depts = required_filters["department"]
            if len(depts) == 1:
                where_clauses.append({"department": depts[0]})
            else:
                where_clauses.append({"department": {"$in": depts}})
        
        # Handle topics 
        # Note: Topics are stored as comma-separated strings in Chroma
        # We can't use substring matching, so we'll be less strict with filters
        # for topics and rely more on vector similarity
        # Skip topic filtering for now - vector search will handle it
        
        # Handle audience - also skip for now
        # Rely on vector similarity to find relevant content
        
        # Combine all clauses with AND
        if not where_clauses:
            return None
        elif len(where_clauses) == 1:
            return where_clauses[0]
        else:
            return {"$and": where_clauses}
    
    def _format_results(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Format ChromaDB results into structured chunks.
        
        Args:
            results: Raw results from ChromaDB
            
        Returns:
            List of formatted chunk dictionaries
        """
        chunks = []
        
        if not results["ids"]:
            return chunks
        
        distances = results["distances"]
        
        # Normalize distances to 0-1 similarity scores
        # Lower distance = higher similarity
        if distances:
            min_dist = min(distances)
            max_dist = max(distances)
            dist_range = max_dist - min_dist if max_dist > min_dist else 1.0
        else:
            min_dist = 0
            dist_range = 1.0
        
        for i in range(len(results["ids"])):
            distance = distances[i]
            
            # Normalize: closest = 1.0, farthest = 0.0
            if dist_range > 0:
                score = 1.0 - ((distance - min_dist) / dist_range)
            else:
                score = 1.0
            
            # Ensure score is in [0, 1]
            score = max(0.0, min(1.0, score))
            
            chunk = {
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "distance": distance,
                "score": score,
            }
            chunks.append(chunk)
        
        return chunks


# Global retriever instance
_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    """
    Get or create the global retriever instance.
    
    Returns:
        Singleton Retriever instance
    """
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever