"""
Document-level metadata extraction using LLM.
Extracts comprehensive metadata for the entire document.
"""

import json
from typing import TYPE_CHECKING, Any

from src.metadata.prompt_loader import get_prompt_loader
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.metadata.classifier import ClassificationResult

logger = get_logger(__name__)


class DocumentMetadataExtractor:
    """
    Extracts document-level metadata using LLM.
    
    Uses the doc_metadata_extraction prompt to analyze full documents
    and extract structured metadata for RAG retrieval.
    """
    
    def __init__(self) -> None:
        self.llm_client = get_llm_client()
        self.prompt_loader = get_prompt_loader()
        
        logger.info("document_metadata_extractor_initialized")
    
    def extract(
        self,
        document_text: str,
        classification: "ClassificationResult",
    ) -> dict[str, Any]:
        """
        Extract document-level metadata.
        
        Args:
            document_text: Full document text
            classification: Pre-computed classification result
            
        Returns:
            Dictionary containing extracted metadata
            
        Raises:
            Exception: If extraction fails
        """
        try:
            logger.info(
                "doc_metadata_extraction_started",
                document_type=classification.document_type,
                complexity=classification.complexity,
                text_length=len(document_text),
            )
        except AttributeError as e:
            logger.error(
                "classification_object_error",
                classification_type=type(classification).__name__,
                classification_value=str(classification)[:200],
                error=str(e),
            )
            raise TypeError(f"Expected ClassificationResult object, got {type(classification).__name__}")
        
        # Prepare classification result as a dictionary for the prompt
        classification_dict = {
            "complexity": classification.complexity,
            "document_type": classification.document_type,
            "requires_deep_analysis": classification.requires_deep_analysis,
            "confidence": classification.confidence,
            "reasoning": classification.reasoning,
        }
        classification_json = json.dumps(classification_dict, indent=2)
        
        # Load and format prompt
        prompt = self.prompt_loader.get_prompt_text(
            "doc_metadata_extraction",
            document_text=document_text,
            classification_result=classification_json,
        )
        
        # Extract metadata using LLM
        try:
            metadata = self.llm_client.complete_json(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=800,  # Allow comprehensive metadata
            )
            
            # Post-process metadata
            metadata = self._post_process_metadata(metadata, classification)
            
            logger.info(
                "doc_metadata_extraction_completed",
                fields_extracted=len(metadata),
                topics_count=len(metadata.get("topics", [])),
                confidence=metadata.get("classification_confidence"),
            )
            
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(
                "doc_metadata_json_parse_failed",
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "doc_metadata_extraction_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
    
    def _post_process_metadata(
        self,
        metadata: dict[str, Any],
        classification: "ClassificationResult",
    ) -> dict[str, Any]:
        """
        Post-process extracted metadata to ensure consistency.
        
        Args:
            metadata: Raw extracted metadata
            classification: Original classification result
            
        Returns:
            Cleaned and validated metadata
        """
        # Ensure document_type matches classification
        if "document_type" not in metadata:
            metadata["document_type"] = classification.document_type
        elif metadata["document_type"] != classification.document_type:
            logger.warning(
                "document_type_mismatch",
                classification=classification.document_type,
                extracted=metadata["document_type"],
            )
            # Trust the classification
            metadata["document_type"] = classification.document_type
        
        # Add classification metadata
        metadata["complexity"] = classification.complexity
        metadata["requires_deep_analysis"] = classification.requires_deep_analysis
        
        # Ensure topics is a list
        if "topics" in metadata and not isinstance(metadata["topics"], list):
            metadata["topics"] = [metadata["topics"]]
        
        # Ensure intended_audience is a list
        if "intended_audience" in metadata and not isinstance(metadata["intended_audience"], list):
            metadata["intended_audience"] = [metadata["intended_audience"]]
        
        # Clean up null/empty values
        metadata = {
            k: v for k, v in metadata.items()
            if v is not None and v != "" and v != []
        }
        
        # Ensure required fields have defaults if missing
        defaults = {
            "requires_acknowledgment": False,
            "compliance_related": False,
            "geographic_scope": ["global"],
        }
        
        for field, default in defaults.items():
            if field not in metadata:
                metadata[field] = default
        
        return metadata


# Global extractor instance
_extractor: DocumentMetadataExtractor | None = None


def get_doc_extractor() -> DocumentMetadataExtractor:
    """
    Get or create the global document metadata extractor instance.
    
    Returns:
        Singleton DocumentMetadataExtractor instance
    """
    global _extractor
    if _extractor is None:
        _extractor = DocumentMetadataExtractor()
    return _extractor