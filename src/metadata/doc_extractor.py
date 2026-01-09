"""Document-level metadata extraction using LLM."""

import json
from typing import TYPE_CHECKING, Any

from src.metadata.prompt_loader import get_prompt_loader
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger
from config.business_rules import get_allowed_topics_for_domain, is_valid_topic_for_domain

if TYPE_CHECKING:
    from src.metadata.classifier import ClassificationResult

logger = get_logger(__name__)


class DocumentMetadataExtractor:
    """Extracts document-level metadata using LLM."""
    
    def __init__(self) -> None:
        self.llm_client = get_llm_client()
        self.prompt_loader = get_prompt_loader()
        logger.info("document_metadata_extractor_initialized")
    
    def extract(
        self,
        document_text: str,
        classification: "ClassificationResult",
    ) -> dict[str, Any]:
        """Extract document-level metadata."""
        
        logger.info(
            "doc_metadata_extraction_started",
            document_type=classification.document_type,
            complexity=classification.complexity,
            text_length=len(document_text),
        )
        
        classification_dict = {
            "domain": classification.domain,
            "complexity": classification.complexity,
            "document_type": classification.document_type,
            "requires_deep_analysis": classification.requires_deep_analysis,
            "confidence": classification.confidence,
            "reasoning": classification.reasoning,
        }
        classification_json = json.dumps(classification_dict, indent=2)
        
        # Get allowed topics for this domain
        allowed_topics = get_allowed_topics_for_domain(classification.domain)
        allowed_topics_str = ", ".join(allowed_topics)
        
        # Load and format prompt
        prompt = self.prompt_loader.get_prompt_text(
            "doc_metadata_extraction",
            document_text=document_text,
            classification_result=classification_json,
            domain=classification.domain,
            allowed_topics=allowed_topics_str,
        )
        
        try:
            metadata = self.llm_client.complete_json(
                prompt=prompt,
                temperature=0.1,
                max_tokens=800,
            )
            
            metadata = self._post_process_metadata(metadata, classification)
            
            logger.info(
                "doc_metadata_extraction_completed",
                domain=metadata.get("domain"),
                fields_extracted=len(metadata),
                topics_count=len(metadata.get("topics", [])),
            )
            
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error("doc_metadata_json_parse_failed", error=str(e))
            raise
        except Exception as e:
            logger.error("doc_metadata_extraction_failed", error=str(e))
            raise
    
    def _validate_topics(
        self,
        topics: list[str],
        domain: str,
    ) -> tuple[list[str], list[str]]:
        """
        Validate topics against domain vocabulary.
        
        Args:
            topics: Extracted topics
            domain: Document domain
            
        Returns:
            Tuple of (valid_topics, invalid_topics)
        """
        valid_topics = []
        invalid_topics = []
        
        for topic in topics:
            if is_valid_topic_for_domain(topic, domain):
                valid_topics.append(topic)
            else:
                invalid_topics.append(topic)
                logger.warning(
                    "invalid_topic_for_domain",
                    topic=topic,
                    domain=domain,
                )
        
        # If all topics are invalid, try to salvage with closest matches
        if not valid_topics and invalid_topics:
            logger.warning(
                "all_topics_invalid",
                domain=domain,
                invalid_topics=invalid_topics,
            )
            
            # Use general fallback topics for the domain
            allowed = get_allowed_topics_for_domain(domain)
            if allowed:
                # Take first 3 topics as generic fallback
                valid_topics = allowed[:3]
                logger.info(
                    "using_fallback_topics",
                    fallback_topics=valid_topics,
                )
        
        return valid_topics, invalid_topics
    
    def _post_process_metadata(
        self,
        metadata: dict[str, Any],
        classification: "ClassificationResult",
    ) -> dict[str, Any]:
        """Post-process extracted metadata to ensure consistency."""
        
        if "domain" not in metadata:
            metadata["domain"] = classification.domain
        elif metadata["domain"] != classification.domain:
            logger.warning(
                "domain_mismatch",
                classification=classification.domain,
                extracted=metadata["domain"],
            )
            metadata["domain"] = classification.domain
        
        if "document_type" not in metadata:
            metadata["document_type"] = classification.document_type
        elif metadata["document_type"] != classification.document_type:
            logger.warning(
                "document_type_mismatch",
                classification=classification.document_type,
                extracted=metadata["document_type"],
            )
            metadata["document_type"] = classification.document_type
        
        metadata["complexity"] = classification.complexity
        metadata["requires_deep_analysis"] = classification.requires_deep_analysis
        
        # Ensure topics is a list
        if "topics" in metadata and not isinstance(metadata["topics"], list):
            metadata["topics"] = [metadata["topics"]]
        
        # Validate topics against domain vocabulary
        if "topics" in metadata and "domain" in metadata:
            valid_topics, invalid_topics = self._validate_topics(
                metadata["topics"],
                metadata["domain"],
            )
            
            if invalid_topics:
                logger.warning(
                    "topics_filtered",
                    domain=metadata["domain"],
                    original_count=len(metadata["topics"]),
                    valid_count=len(valid_topics),
                    invalid_topics=invalid_topics,
                )
            
            metadata["topics"] = valid_topics
        
        if "intended_audience" in metadata and not isinstance(metadata["intended_audience"], list):
            metadata["intended_audience"] = [metadata["intended_audience"]]
        
        metadata = {k: v for k, v in metadata.items() if v is not None and v != "" and v != []}
        
        defaults = {
            "requires_acknowledgment": False,
            "compliance_related": False,
            "geographic_scope": ["global"],
        }
        for field, default in defaults.items():
            if field not in metadata:
                metadata[field] = default
        
        return metadata


_extractor: DocumentMetadataExtractor | None = None


def get_doc_extractor() -> DocumentMetadataExtractor:
    """Get or create the global document metadata extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = DocumentMetadataExtractor()
    return _extractor