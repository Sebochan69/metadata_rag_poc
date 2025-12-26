"""
OpenAI API client with retry logic, error handling, and token tracking.
Provides a robust wrapper for all LLM calls in the application.
"""

import json
from typing import Any, Literal

from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    Wrapper for OpenAI API with retry logic and error handling.
    
    Features:
    - Automatic retries with exponential backoff
    - Token usage tracking
    - Structured error handling
    - Temperature and model configuration
    """
    
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.request_timeout,
        )
        self.total_tokens_used = 0
        self.total_cost = 0.0
    
    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=settings.retry_wait_seconds,
            min=1,
            max=10
        ),
        reraise=True,
    )
    def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: Literal["text", "json_object"] = "text",
        system_message: str | None = None,
    ) -> str:
        """
        Generate a completion from OpenAI with retry logic.
        
        Args:
            prompt: User prompt
            model: Model name (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Maximum tokens to generate
            response_format: "text" or "json_object" for structured output
            system_message: Optional system message
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If all retry attempts fail
        """
        # Use defaults from settings if not provided
        model = model or settings.openai_model_doc_extraction
        temperature = temperature or settings.llm_temperature_extraction
        max_tokens = max_tokens or settings.llm_max_tokens_extraction
        
        # Build messages
        messages: list[dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare API call parameters
        api_params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Add response format for JSON mode
        if response_format == "json_object":
            api_params["response_format"] = {"type": "json_object"}
        
        logger.info(
            "llm_call_started",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_length=len(prompt),
        )
        
        try:
            response = self.client.chat.completions.create(**api_params)
            
            # Extract response
            content = response.choices[0].message.content or ""
            
            # Track usage
            if response.usage:
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                
                # Estimate cost (approximate - update with current pricing)
                cost = self._estimate_cost(model, response.usage)
                self.total_cost += cost
                
                logger.info(
                    "llm_call_completed",
                    model=model,
                    tokens_used=tokens_used,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    estimated_cost=f"${cost:.4f}",
                    total_cost=f"${self.total_cost:.4f}",
                )
            
            return content
            
        except Exception as e:
            logger.error(
                "llm_call_failed",
                model=model,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
    
    def complete_json(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a JSON completion from OpenAI.
        
        Automatically uses json_object response format and parses the result.
        
        Args:
            prompt: User prompt (should request JSON output)
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_message: Optional system message
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        response = self.complete(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="json_object",
            system_message=system_message,
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(
                "json_parse_failed",
                response=response[:500],  # Log first 500 chars
                error=str(e),
            )
            raise
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info("embedding_started", text_count=len(texts))
        
        try:
            response = self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=texts,
            )
            
            embeddings = [item.embedding for item in response.data]
            
            # Track usage
            if response.usage:
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                
                logger.info(
                    "embedding_completed",
                    text_count=len(texts),
                    tokens_used=tokens_used,
                )
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "embedding_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
    
    def _estimate_cost(self, model: str, usage: Any) -> float:
        """
        Estimate API call cost based on token usage.
        
        Pricing as of December 2024 (update as needed):
        - GPT-4o: $2.50/$10.00 per 1M tokens (input/output)
        - GPT-4o-mini: $0.150/$0.600 per 1M tokens
        - text-embedding-3-small: $0.020 per 1M tokens
        """
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        
        # Pricing per 1M tokens
        pricing = {
            "gpt-4o": (2.50, 10.00),
            "gpt-4o-mini": (0.150, 0.600),
            "text-embedding-3-small": (0.020, 0.020),
            "text-embedding-3-large": (0.130, 0.130),
        }
        
        # Get pricing or use default
        input_price, output_price = pricing.get(model, (2.50, 10.00))
        
        # Calculate cost
        cost = (
            (prompt_tokens / 1_000_000) * input_price +
            (completion_tokens / 1_000_000) * output_price
        )
        
        return cost
    
    def get_usage_stats(self) -> dict[str, Any]:
        """
        Get cumulative usage statistics.
        
        Returns:
            Dictionary with total tokens and estimated cost
        """
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost": f"${self.total_cost:.4f}",
        }
    
    def reset_usage_stats(self) -> None:
        """Reset usage tracking counters."""
        self.total_tokens_used = 0
        self.total_cost = 0.0
        logger.info("usage_stats_reset")


# Global client instance
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """
    Get or create the global LLM client instance.
    
    Returns:
        Singleton LLMClient instance
    """
    global _client
    if _client is None:
        _client = LLMClient()
        logger.info("llm_client_initialized")
    return _client