"""
Metadata validation using JSON schema and business rules.
Ensures all extracted metadata conforms to required standards.
"""

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, ValidationError as JSONSchemaValidationError

from config.business_rules import (
    AUTHORITY_LEVELS,
    DEPARTMENTS,
    DOCUMENT_TYPES,
    INTENDED_AUDIENCES,
    ValidationRules,
    validate_metadata_completeness,
)
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MetadataValidationError(Exception):
    """Raised when metadata validation fails"""
    
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s)")


class MetadataValidator:
    """
    Validates metadata against JSON schema and business rules.
    
    Performs two-stage validation:
    1. JSON Schema validation (structure, types, required fields)
    2. Business rules validation (controlled vocabularies, constraints)
    """
    
    def __init__(self, schema_path: Path | None = None) -> None:
        """
        Initialize validator with JSON schema.
        
        Args:
            schema_path: Path to metadata_schema.json
                        (defaults to config/metadata_schema.json)
        """
        if schema_path is None:
            schema_path = Path("config") / "metadata_schema.json"
        
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
        
        logger.info(
            "metadata_validator_initialized",
            schema_path=str(schema_path),
        )
    
    def _load_schema(self) -> dict[str, Any]:
        """Load JSON schema from file"""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {self.schema_path}")
        
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def validate(
        self,
        metadata: dict[str, Any],
        strict: bool = True,
        fix_minor_issues: bool = True,
    ) -> dict[str, Any]:
        """
        Validate metadata and optionally fix minor issues.
        
        Args:
            metadata: Metadata dictionary to validate
            strict: If True, raise exception on validation errors
            fix_minor_issues: If True, attempt to fix minor issues
                             (e.g., trim whitespace, lowercase enums)
            
        Returns:
            Validated (and possibly fixed) metadata
            
        Raises:
            MetadataValidationError: If validation fails and strict=True
        """
        logger.debug("validating_metadata", strict=strict, fix=fix_minor_issues)
        
        # Stage 1: Fix minor issues if enabled
        if fix_minor_issues:
            metadata = self._fix_minor_issues(metadata)
        
        # Stage 2: JSON Schema validation
        schema_errors = self._validate_schema(metadata)
        
        # Stage 3: Business rules validation
        business_errors = self._validate_business_rules(metadata)
        
        # Combine errors
        all_errors = schema_errors + business_errors
        
        if all_errors:
            logger.warning(
                "metadata_validation_failed",
                error_count=len(all_errors),
                errors=all_errors[:5],  # Log first 5 errors
            )
            
            if strict:
                raise MetadataValidationError(all_errors)
        else:
            logger.info("metadata_validation_passed")
        
        return metadata
    
    def _fix_minor_issues(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Attempt to fix common minor issues.
        
        Fixes:
        - Trim whitespace from strings
        - Lowercase enum values
        - Remove empty arrays
        - Convert single values to arrays where needed
        """
        fixed = metadata.copy()
        
        # Trim string fields
        string_fields = [
            "document_type",
            "department",
            "authority_level",
            "version",
            "document_summary",
        ]
        for field in string_fields:
            if field in fixed and isinstance(fixed[field], str):
                fixed[field] = fixed[field].strip()
        
        # Lowercase enum fields
        enum_fields = ["authority_level"]
        for field in enum_fields:
            if field in fixed and isinstance(fixed[field], str):
                fixed[field] = fixed[field].lower()
        
        # Ensure arrays
        array_fields = ["topics", "intended_audience", "key_entities"]
        for field in array_fields:
            if field in fixed:
                if not isinstance(fixed[field], list):
                    # Convert single value to array
                    fixed[field] = [fixed[field]]
                # Remove duplicates and empty strings
                fixed[field] = [
                    item.strip() if isinstance(item, str) else item
                    for item in fixed[field]
                    if item and (not isinstance(item, str) or item.strip())
                ]
        
        # Remove empty optional fields
        optional_empty_fields = [
            "key_entities",
            "geographic_scope",
            "expiration_date",
        ]
        for field in optional_empty_fields:
            if field in fixed and not fixed[field]:
                del fixed[field]
        
        return fixed
    
    def _validate_schema(self, metadata: dict[str, Any]) -> list[str]:
        """Validate against JSON schema"""
        errors = []
        
        for error in self.validator.iter_errors(metadata):
            error_msg = self._format_schema_error(error)
            errors.append(error_msg)
        
        return errors
    
    def _format_schema_error(self, error: JSONSchemaValidationError) -> str:
        """Format JSON schema error for readability"""
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        return f"{path}: {error.message}"
    
    def _validate_business_rules(self, metadata: dict[str, Any]) -> list[str]:
        """Validate against business rules"""
        errors = []
        
        # Use business_rules validation
        errors.extend(validate_metadata_completeness(metadata))
        
        # Version format
        if "version" in metadata:
            if not re.match(ValidationRules.VERSION_PATTERN, metadata["version"]):
                errors.append(
                    f"Invalid version format: {metadata['version']}. "
                    "Expected format: major.minor or major.minor.patch"
                )
        
        # Date format
        date_fields = ["effective_date", "expiration_date"]
        for field in date_fields:
            if field in metadata and metadata[field]:
                if not re.match(ValidationRules.DATE_PATTERN, metadata[field]):
                    errors.append(
                        f"Invalid {field} format: {metadata[field]}. "
                        "Expected format: YYYY-MM-DD"
                    )
        
        # Summary length
        if "document_summary" in metadata:
            summary = metadata["document_summary"]
            if len(summary) < ValidationRules.MIN_SUMMARY_LENGTH:
                errors.append(
                    f"Summary too short: {len(summary)} characters. "
                    f"Minimum: {ValidationRules.MIN_SUMMARY_LENGTH}"
                )
            if len(summary) > ValidationRules.MAX_SUMMARY_LENGTH:
                errors.append(
                    f"Summary too long: {len(summary)} characters. "
                    f"Maximum: {ValidationRules.MAX_SUMMARY_LENGTH}"
                )
        
        # Confidence range
        if "classification_confidence" in metadata:
            conf = metadata["classification_confidence"]
            if not (ValidationRules.MIN_CONFIDENCE <= conf <= ValidationRules.MAX_CONFIDENCE):
                errors.append(
                    f"Confidence out of range: {conf}. "
                    f"Must be between {ValidationRules.MIN_CONFIDENCE} and "
                    f"{ValidationRules.MAX_CONFIDENCE}"
                )
        
        # Check expiration_date is after effective_date
        if (
            "effective_date" in metadata
            and "expiration_date" in metadata
            and metadata["effective_date"]
            and metadata["expiration_date"]
        ):
            if metadata["expiration_date"] <= metadata["effective_date"]:
                errors.append(
                    "expiration_date must be after effective_date"
                )
        
        return errors
    
    def validate_chunk_metadata(
        self,
        chunk_metadata: dict[str, Any],
        strict: bool = True,
    ) -> dict[str, Any]:
        """
        Validate chunk-level metadata.
        
        Args:
            chunk_metadata: Chunk metadata to validate
            strict: If True, raise exception on errors
            
        Returns:
            Validated chunk metadata
        """
        errors = []
        
        # Section topics
        if "section_topics" in chunk_metadata:
            topics = chunk_metadata["section_topics"]
            if len(topics) > ValidationRules.MAX_SECTION_TOPICS:
                errors.append(
                    f"Too many section topics: {len(topics)}. "
                    f"Maximum: {ValidationRules.MAX_SECTION_TOPICS}"
                )
        
        # Reference links
        if "reference_links" in chunk_metadata:
            links = chunk_metadata["reference_links"]
            if len(links) > ValidationRules.MAX_REFERENCE_LINKS:
                errors.append(
                    f"Too many reference links: {len(links)}. "
                    f"Maximum: {ValidationRules.MAX_REFERENCE_LINKS}"
                )
        
        # Chunk number should be non-negative
        if "chunk_number" in chunk_metadata:
            if chunk_metadata["chunk_number"] < 0:
                errors.append("chunk_number cannot be negative")
        
        if errors:
            logger.warning(
                "chunk_metadata_validation_failed",
                errors=errors,
            )
            if strict:
                raise MetadataValidationError(errors)
        
        return chunk_metadata
    
    def is_high_confidence(self, metadata: dict[str, Any]) -> bool:
        """Check if metadata has high confidence score"""
        if "classification_confidence" not in metadata:
            return False
        return (
            metadata["classification_confidence"]
            >= ValidationRules.HIGH_CONFIDENCE_THRESHOLD
        )
    
    def is_low_confidence(self, metadata: dict[str, Any]) -> bool:
        """Check if metadata has low confidence score (needs review)"""
        if "classification_confidence" not in metadata:
            return True
        return (
            metadata["classification_confidence"]
            < ValidationRules.LOW_CONFIDENCE_THRESHOLD
        )
    
    def get_validation_summary(
        self, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Get validation summary without raising exceptions.
        
        Returns:
            Dictionary with validation results and statistics
        """
        try:
            self.validate(metadata, strict=False)
            is_valid = True
            errors = []
        except Exception as e:
            is_valid = False
            errors = getattr(e, "errors", [str(e)])
        
        return {
            "is_valid": is_valid,
            "error_count": len(errors),
            "errors": errors,
            "is_high_confidence": self.is_high_confidence(metadata),
            "is_low_confidence": self.is_low_confidence(metadata),
            "has_required_fields": all(
                field in metadata
                for field in [
                    "document_type",
                    "department",
                    "authority_level",
                    "topics",
                    "intended_audience",
                ]
            ),
        }


# Global validator instance
_validator: MetadataValidator | None = None


def get_validator() -> MetadataValidator:
    """
    Get or create the global validator instance.
    
    Returns:
        Singleton MetadataValidator instance
    """
    global _validator
    if _validator is None:
        _validator = MetadataValidator()
    return _validator