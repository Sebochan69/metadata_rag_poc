"""
Text embedding generation using OpenAI.
Provides efficient batching and caching for embeddings.
"""

from typing import Any

from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Embedder:
    """
    Generates embeddings for text using OpenAI's embedding models.
    
    Features:
    - Batch processing for efficiency
    - Automatic chunking for API limits
    - Token tracking
    """
    
    def __init__(self) -> None:
        self.llm_client = get_llm_client()
        logger.info("embedder_initialized")
    
    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to embed per API call
                       (OpenAI limit is 2048, we use 100 for safety)
            
        Returns:
            List of embedding vectors (one per text)
        """
        if not texts:
            return []
        
        logger.info(
            "embedding_started",
            text_count=len(texts),
            batch_size=batch_size,
        )
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            logger.debug(
                "embedding_batch",
                batch_num=i // batch_size + 1,
                batch_size=len(batch),
            )
            
            # Get embeddings from LLM client
            embeddings = self.llm_client.embed(batch)
            all_embeddings.extend(embeddings)
        
        logger.info(
            "embedding_completed",
            embeddings_generated=len(all_embeddings),
        )
        
        return all_embeddings
    
    def embed_single(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.embed_texts([text])
        return embeddings[0]


# Global embedder instance
_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """
    Get or create the global embedder instance.
    
    Returns:
        Singleton Embedder instance
    """
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder