"""
Business rules and controlled vocabularies for metadata validation.
Defines allowed values for metadata fields to ensure consistency.
"""

from typing import Final

# ============================================================================
# Document Types
# ============================================================================

DOCUMENT_TYPES: Final[list[str]] = [
    "HR Policy",
    "Technical Manual",
    "Financial Report",
    "Legal Document",
    "Memo",
    "Procedure",
    "Guideline",
    "Standard Operating Procedure",
    "Other",
]

# ============================================================================
# Departments
# ============================================================================

DEPARTMENTS: Final[list[str]] = [
    "HR",
    "Engineering",
    "Finance",
    "Legal",
    "Operations",
    "Marketing",
    "Sales",
    "Executive",
    "IT",
    "Cross-Functional",
]

# ============================================================================
# Authority Levels
# ============================================================================

AUTHORITY_LEVELS: Final[list[str]] = [
    "official",      # Current, approved, authoritative
    "draft",         # Under review, not yet approved
    "archived",      # Historical, superseded by newer version
    "deprecated",    # No longer in use, kept for reference
    "reference",     # Informational, not authoritative
]

# ============================================================================
# Intended Audience
# ============================================================================

INTENDED_AUDIENCES: Final[list[str]] = [
    "all_employees",
    "managers",
    "executives",
    "engineers",
    "hr_staff",
    "finance_team",
    "legal_team",
    "contractors",
    "new_hires",
    "specific_department",
]

# ============================================================================
# Geographic Scope
# ============================================================================

GEOGRAPHIC_SCOPES: Final[list[str]] = [
    "global",
    "us",
    "eu",
    "apac",
    "emea",
    "country_specific",
]

# ============================================================================
# Complexity Levels (from classification)
# ============================================================================

COMPLEXITY_LEVELS: Final[list[str]] = [
    "simple",
    "structured",
    "complex",
]

# ============================================================================
# Section Types (for chunk-level metadata)
# ============================================================================

SECTION_TYPES: Final[list[str]] = [
    "overview",
    "procedure",
    "example",
    "definition",
    "requirement",
    "recommendation",
    "reference",
    "warning",
    "best_practice",
]

# ============================================================================
# Common Topics (Hierarchical)
# ============================================================================

# Topic taxonomy with hierarchical structure
TOPIC_TAXONOMY: Final[dict[str, list[str]]] = {
    # HR Topics
    "hr": [
        "annual_leave",
        "sick_leave",
        "parental_leave",
        "bereavement_leave",
        "unpaid_leave",
        "remote_work",
        "hybrid_work",
        "performance_review",
        "compensation",
        "benefits",
        "equity",
        "stock_options",
        "vesting",
        "employee_conduct",
        "code_of_conduct",
        "harassment_policy",
        "diversity_inclusion",
        "onboarding",
        "offboarding",
        "termination",
    ],
    # Technical Topics
    "engineering": [
        "api_documentation",
        "system_architecture",
        "deployment",
        "ci_cd",
        "kubernetes",
        "docker",
        "cloud_infrastructure",
        "aws",
        "azure",
        "gcp",
        "database",
        "security",
        "authentication",
        "authorization",
        "testing",
        "code_review",
        "git_workflow",
        "monitoring",
        "logging",
        "incident_response",
    ],
    # Finance Topics
    "finance": [
        "budget",
        "expenses",
        "revenue",
        "forecasting",
        "quarterly_report",
        "annual_report",
        "financial_planning",
        "cost_center",
        "procurement",
        "vendor_management",
        "invoicing",
        "reimbursement",
        "travel_expenses",
    ],
    # Legal Topics
    "legal": [
        "contract",
        "agreement",
        "terms_of_service",
        "privacy_policy",
        "data_protection",
        "gdpr",
        "ccpa",
        "intellectual_property",
        "trademark",
        "copyright",
        "patent",
        "liability",
        "indemnification",
        "compliance",
        "regulatory",
    ],
    # Operations Topics
    "operations": [
        "standard_operating_procedure",
        "sop",
        "process_documentation",
        "quality_assurance",
        "supply_chain",
        "inventory",
        "logistics",
        "facilities",
        "safety",
        "emergency_procedures",
    ],
}

# Flattened list of all topics
ALL_TOPICS: Final[list[str]] = [
    topic for topics in TOPIC_TAXONOMY.values() for topic in topics
]

# ============================================================================
# Validation Rules
# ============================================================================

class ValidationRules:
    """Business rules for metadata validation"""
    
    # Version format: major.minor.patch
    VERSION_PATTERN: Final[str] = r"^\d+\.\d+(\.\d+)?$"
    
    # Date format: YYYY-MM-DD
    DATE_PATTERN: Final[str] = r"^\d{4}-\d{2}-\d{2}$"
    
    # Minimum/maximum values
    MIN_SUMMARY_LENGTH: Final[int] = 50
    MAX_SUMMARY_LENGTH: Final[int] = 500
    MIN_TOPICS: Final[int] = 1
    MAX_TOPICS: Final[int] = 10
    MAX_KEY_ENTITIES: Final[int] = 20
    
    # Confidence thresholds
    MIN_CONFIDENCE: Final[float] = 0.0
    MAX_CONFIDENCE: Final[float] = 1.0
    LOW_CONFIDENCE_THRESHOLD: Final[float] = 0.7
    HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.9
    
    # Chunk metadata
    MAX_SECTION_TOPICS: Final[int] = 5
    MAX_REFERENCE_LINKS: Final[int] = 10


# ============================================================================
# Helper Functions
# ============================================================================

def is_valid_document_type(doc_type: str) -> bool:
    """Check if document type is in allowed list"""
    return doc_type in DOCUMENT_TYPES


def is_valid_department(department: str) -> bool:
    """Check if department is in allowed list"""
    return department in DEPARTMENTS


def is_valid_authority_level(level: str) -> bool:
    """Check if authority level is in allowed list"""
    return level in AUTHORITY_LEVELS


def is_valid_audience(audience: str) -> bool:
    """Check if audience is in allowed list"""
    return audience in INTENDED_AUDIENCES


def is_valid_topic(topic: str) -> bool:
    """Check if topic is in allowed list"""
    return topic.lower() in [t.lower() for t in ALL_TOPICS]


def get_topic_category(topic: str) -> str | None:
    """
    Get the category (hr, engineering, etc.) for a given topic.
    
    Args:
        topic: Topic name to look up
        
    Returns:
        Category name or None if not found
    """
    topic_lower = topic.lower()
    for category, topics in TOPIC_TAXONOMY.items():
        if topic_lower in [t.lower() for t in topics]:
            return category
    return None


def get_related_topics(topic: str, max_results: int = 5) -> list[str]:
    """
    Get topics related to the given topic (from same category).
    
    Args:
        topic: Topic name
        max_results: Maximum number of related topics to return
        
    Returns:
        List of related topic names
    """
    category = get_topic_category(topic)
    if not category:
        return []
    
    # Get all topics in same category except the input topic
    related = [
        t for t in TOPIC_TAXONOMY[category]
        if t.lower() != topic.lower()
    ]
    
    return related[:max_results]


def suggest_topics(partial: str, max_suggestions: int = 10) -> list[str]:
    """
    Suggest topics based on partial string match.
    
    Args:
        partial: Partial topic name
        max_suggestions: Maximum suggestions to return
        
    Returns:
        List of matching topic names
    """
    partial_lower = partial.lower()
    matches = [
        topic for topic in ALL_TOPICS
        if partial_lower in topic.lower()
    ]
    return matches[:max_suggestions]


def validate_metadata_completeness(metadata: dict) -> list[str]:
    """
    Check if required metadata fields are present and valid.
    
    Args:
        metadata: Metadata dictionary to validate
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = [
        "document_type",
        "department",
        "authority_level",
        "topics",
        "intended_audience",
    ]
    
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
    
    # Validate field values
    if "document_type" in metadata:
        if not is_valid_document_type(metadata["document_type"]):
            errors.append(
                f"Invalid document_type: {metadata['document_type']}. "
                f"Must be one of: {', '.join(DOCUMENT_TYPES)}"
            )
    
    if "department" in metadata:
        if not is_valid_department(metadata["department"]):
            errors.append(
                f"Invalid department: {metadata['department']}. "
                f"Must be one of: {', '.join(DEPARTMENTS)}"
            )
    
    if "authority_level" in metadata:
        if not is_valid_authority_level(metadata["authority_level"]):
            errors.append(
                f"Invalid authority_level: {metadata['authority_level']}. "
                f"Must be one of: {', '.join(AUTHORITY_LEVELS)}"
            )
    
    # Validate arrays
    if "topics" in metadata:
        if not isinstance(metadata["topics"], list):
            errors.append("topics must be an array")
        elif len(metadata["topics"]) < ValidationRules.MIN_TOPICS:
            errors.append(f"Must have at least {ValidationRules.MIN_TOPICS} topic")
        elif len(metadata["topics"]) > ValidationRules.MAX_TOPICS:
            errors.append(f"Cannot have more than {ValidationRules.MAX_TOPICS} topics")
    
    if "intended_audience" in metadata:
        if not isinstance(metadata["intended_audience"], list):
            errors.append("intended_audience must be an array")
        else:
            for audience in metadata["intended_audience"]:
                if not is_valid_audience(audience):
                    errors.append(f"Invalid audience: {audience}")
    
    return errors


# ============================================================================
# Export all constants for easy import
# ============================================================================

__all__ = [
    "DOCUMENT_TYPES",
    "DEPARTMENTS",
    "AUTHORITY_LEVELS",
    "INTENDED_AUDIENCES",
    "GEOGRAPHIC_SCOPES",
    "COMPLEXITY_LEVELS",
    "SECTION_TYPES",
    "TOPIC_TAXONOMY",
    "ALL_TOPICS",
    "ValidationRules",
    "is_valid_document_type",
    "is_valid_department",
    "is_valid_authority_level",
    "is_valid_audience",
    "is_valid_topic",
    "get_topic_category",
    "get_related_topics",
    "suggest_topics",
    "validate_metadata_completeness",
]