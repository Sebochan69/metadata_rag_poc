"""
Answer generation from retrieved context.
Synthesizes answers using LLM based on relevant document chunks.
"""

from typing import Any

from src.metadata.prompt_loader import get_prompt_loader
from src.retrieval.retriever import QueryResult
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Answer:
    """
    Generated answer with metadata.
    
    Attributes:
        query: Original user query
        answer: Generated answer text
        sources: List of source chunks used
        confidence: Answer confidence (based on retrieval scores)
        context_used: Number of chunks used for generation
    """
    
    def __init__(
        self,
        query: str,
        answer: str,
        sources: list[dict[str, Any]],
        confidence: float,
    ) -> None:
        self.query = query
        self.answer = answer
        self.sources = sources
        self.confidence = confidence
        self.context_used = len(sources)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "context_used": self.context_used,
        }
    
    def __str__(self) -> str:
        """String representation"""
        return self.answer


class AnswerGenerator:
    """
    Generates answers from retrieved context using LLM.
    
    Features:
    - Context formatting
    - Source attribution
    - Confidence scoring
    """
    
    def __init__(self) -> None:
        self.llm_client = get_llm_client()
        self.prompt_loader = get_prompt_loader()
        
        logger.info("answer_generator_initialized")
    
    def generate(
        self,
        query: str,
        retrieval_result: QueryResult,
    ) -> Answer:
        """
        Generate an answer from retrieval results.
        
        Args:
            query: User's query
            retrieval_result: Results from retrieval
            
        Returns:
            Answer object with generated text and sources
        """
        logger.info(
            "answer_generation_started",
            query=query,
            chunks_available=len(retrieval_result.chunks),
        )
        
        # Format context from retrieved chunks
        context = self._format_context(retrieval_result.chunks)
        
        # Load and format prompt
        prompt = self.prompt_loader.get_prompt_text(
            "answer_generation",
            query=query,
            context=context,
        )
        
        # Generate answer
        try:
            answer_text = self.llm_client.complete(
                prompt=prompt,
                temperature=0.3,  # Some creativity but mostly factual
                max_tokens=1000,
            )
            
            # Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(retrieval_result.chunks)
            
            # Prepare source information
            sources = self._prepare_sources(retrieval_result.chunks)
            
            logger.info(
                "answer_generation_completed",
                query=query,
                answer_length=len(answer_text),
                sources_used=len(sources),
                confidence=confidence,
            )
            
            return Answer(
                query=query,
                answer=answer_text,
                sources=sources,
                confidence=confidence,
            )
            
        except Exception as e:
            logger.error(
                "answer_generation_failed",
                query=query,
                error=str(e),
            )
            raise
    
    def _format_context(self, chunks: list[dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context for the LLM.
        
        Args:
            chunks: List of retrieved chunks with metadata
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant documents found."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk["metadata"]
            
            # Build source description
            source_parts = []
            
            if "document_type" in metadata:
                source_parts.append(metadata["document_type"])
            
            if "department" in metadata:
                source_parts.append(metadata["department"])
            
            if "authority_level" in metadata:
                source_parts.append(f"Authority: {metadata['authority_level']}")
            
            source_description = " | ".join(source_parts)
            
            # Format chunk
            context_parts.append(
                f"---\n"
                f"Source: {source_description}\n"
                f"Content: {chunk['text']}\n"
                f"---"
            )
        
        return "\n\n".join(context_parts)
    
    def _calculate_confidence(self, chunks: list[dict[str, Any]]) -> float:
        """
        Calculate confidence score based on retrieval results.
        
        Args:
            chunks: Retrieved chunks with scores
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not chunks:
            return 0.0
        
        # Use average of top 3 scores (or all if fewer)
        top_scores = [chunk["score"] for chunk in chunks[:3]]
        avg_score = sum(top_scores) / len(top_scores)
        
        # Confidence factors:
        # - High similarity scores = higher confidence
        # - Multiple high-scoring chunks = higher confidence
        # - Official/authoritative sources = higher confidence
        
        confidence = avg_score
        
        # Boost if we have multiple good results
        if len(chunks) >= 3 and all(s > 0.7 for s in top_scores):
            confidence = min(1.0, confidence + 0.1)
        
        # Boost if sources are official
        official_count = sum(
            1 for chunk in chunks[:3]
            if chunk["metadata"].get("authority_level") == "official"
        )
        if official_count >= 2:
            confidence = min(1.0, confidence + 0.05)
        
        return round(confidence, 2)
    
    def _prepare_sources(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Prepare source information for attribution.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            List of source dictionaries
        """
        sources = []
        
        for chunk in chunks:
            metadata = chunk["metadata"]
            
            source = {
                "document_id": metadata.get("document_id", "Unknown"),
                "document_type": metadata.get("document_type", "Unknown"),
                "department": metadata.get("department", "Unknown"),
                "authority_level": metadata.get("authority_level", "Unknown"),
                "score": chunk["score"],
            }
            
            # Add optional fields if present
            if "effective_date" in metadata:
                source["effective_date"] = metadata["effective_date"]
            
            if "version" in metadata:
                source["version"] = metadata["version"]
            
            sources.append(source)
        
        return sources


# Global generator instance
_generator: AnswerGenerator | None = None


def get_answer_generator() -> AnswerGenerator:
    """
    Get or create the global answer generator instance.
    
    Returns:
        Singleton AnswerGenerator instance
    """
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator