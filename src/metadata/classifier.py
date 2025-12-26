"""
Document classification using LLM.
Determines document complexity and type to route to appropriate extraction pipeline.
"""

import json
from typing import Any

from config.business_rules import COMPLEXITY_LEVELS, DOCUMENT_TYPES
from src.metadata.prompt_loader import get_prompt_loader
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClassificationResult:
    """
    Structured result from document classification.
    
    Attributes:
        complexity: Document complexity level (simple, structured, complex)
        document_type: Document category
        requires_deep_analysis: Whether deep metadata extraction is needed
        confidence: Classification confidence (0.0-1.0)
        reasoning: Explanation for classification
        raw_response: Original LLM response
    """
    
    def __init__(
        self,
        complexity: str,
        document_type: str,
        requires_deep_analysis: bool,
        confidence: float,
        reasoning: str,
        raw_response: dict[str, Any],
    ) -> None:
        self.complexity = complexity
        self.document_type = document_type
        self.requires_deep_analysis = requires_deep_analysis
        self.confidence = confidence
        self.reasoning = reasoning
        self.raw_response = raw_response
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "complexity": self.complexity,
            "document_type": self.document_type,
            "requires_deep_analysis": self.requires_deep_analysis,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }
    
    def __repr__(self) -> str:
        return (
            f"ClassificationResult(type={self.document_type}, "
            f"complexity={self.complexity}, confidence={self.confidence:.2f})"
        )


class DocumentClassifier:
    """
    Classifies documents using LLM to determine extraction strategy.
    
    Uses the classification prompt to analyze document previews and
    determine complexity, type, and whether deep analysis is required.
    """
    
    def __init__(self) -> None:
        self.llm_client = get_llm_client()
        self.prompt_loader = get_prompt_loader()
        
        logger.info("document_classifier_initialized")
    
    def classify(
        self,
        document_text: str,
        preview_length: int = 2000,
    ) -> ClassificationResult:
        """
        Classify a document.
        
        Args:
            document_text: Full document text
            preview_length: Number of characters to use for preview
                           (default: 2000, ~500 words)
            
        Returns:
            ClassificationResult with type, complexity, and metadata
            
        Raises:
            Exception: If LLM call fails or response is invalid
        """
        logger.info(
            "classification_started",
            text_length=len(document_text),
            preview_length=preview_length,
        )
        
        # Create preview (first pages + last page for context)
        preview = self._create_preview(document_text, preview_length)
        
        # Load and format prompt
        prompt = self.prompt_loader.get_prompt_text(
            "classification",
            document_preview=preview,
        )
        
        # Get classification from LLM
        try:
            response = self.llm_client.complete_json(
                prompt=prompt,
                model=None,  # Uses default from settings
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=250,
            )
            
            # Parse and validate response
            result = self._parse_classification(response)
            
            logger.info(
                "classification_completed",
                document_type=result.document_type,
                complexity=result.complexity,
                confidence=result.confidence,
                requires_deep=result.requires_deep_analysis,
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(
                "classification_json_parse_failed",
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "classification_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
    
    def _create_preview(self, text: str, max_length: int) -> str:
        """
        Create a representative preview of the document.
        
        Strategy: Include beginning and end of document for context.
        - First 80% of preview: beginning of document
        - Last 20% of preview: end of document
        
        This captures title, headers, and conclusion/signature.
        """
        if len(text) <= max_length:
            return text
        
        # Split preview allocation
        start_length = int(max_length * 0.8)
        end_length = max_length - start_length
        
        # Extract start and end
        start = text[:start_length]
        end = text[-end_length:]
        
        # Combine with separator
        preview = f"{start}\n\n[... middle content omitted ...]\n\n{end}"
        
        return preview
    
    def _parse_classification(
        self, response: dict[str, Any]
    ) -> ClassificationResult:
        """
        Parse and validate LLM classification response.
        
        Args:
            response: JSON response from LLM
            
        Returns:
            ClassificationResult object
            
        Raises:
            ValueError: If response is invalid or missing required fields
        """
        # Validate required fields
        required_fields = [
            "complexity",
            "document_type",
            "requires_deep_analysis",
            "confidence",
        ]
        
        missing = [f for f in required_fields if f not in response]
        if missing:
            raise ValueError(
                f"Classification response missing required fields: {missing}"
            )
        
        # Extract fields
        complexity = response["complexity"]
        document_type = response["document_type"]
        requires_deep = response["requires_deep_analysis"]
        confidence = response["confidence"]
        reasoning = response.get("reasoning", "No reasoning provided")
        
        # Validate values
        if complexity not in COMPLEXITY_LEVELS:
            logger.warning(
                "invalid_complexity_level",
                received=complexity,
                allowed=COMPLEXITY_LEVELS,
            )
            # Try to recover by defaulting to structured
            complexity = "structured"
        
        if document_type not in DOCUMENT_TYPES:
            logger.warning(
                "invalid_document_type",
                received=document_type,
                allowed=DOCUMENT_TYPES,
            )
            # Default to "Other" if invalid
            document_type = "Other"
        
        # Validate confidence range
        if not (0.0 <= confidence <= 1.0):
            logger.warning(
                "confidence_out_of_range",
                received=confidence,
            )
            confidence = max(0.0, min(1.0, confidence))  # Clamp to range
        
        # Create result
        return ClassificationResult(
            complexity=complexity,
            document_type=document_type,
            requires_deep_analysis=requires_deep,
            confidence=confidence,
            reasoning=reasoning,
            raw_response=response,
        )
    
    def get_extraction_strategy(
        self, classification: ClassificationResult
    ) -> str:
        """
        Determine extraction strategy based on classification.
        
        Args:
            classification: Classification result
            
        Returns:
            Strategy name: "fast", "template", or "deep"
        """
        if classification.complexity == "simple":
            return "fast"
        elif classification.complexity == "structured":
            return "template"
        else:  # complex
            return "deep"
    
    def should_extract_chunk_metadata(
        self, classification: ClassificationResult
    ) -> bool:
        """
        Determine if chunk-level metadata extraction is needed.
        
        Args:
            classification: Classification result
            
        Returns:
            True if chunk metadata should be extracted
        """
        # Extract chunk metadata if:
        # 1. Document requires deep analysis, OR
        # 2. Document is complex
        return (
            classification.requires_deep_analysis
            or classification.complexity == "complex"
        )


# Global classifier instance
_classifier: DocumentClassifier | None = None


def get_classifier() -> DocumentClassifier:
    """
    Get or create the global classifier instance.
    
    Returns:
        Singleton DocumentClassifier instance
    """
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
    return _classifier