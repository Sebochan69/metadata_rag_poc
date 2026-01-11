"""
Business rules and controlled vocabularies for metadata validation.
Defines allowed values for metadata fields to ensure consistency.
"""

from typing import Final

# ============================================================================
# Domains (NEW - Phase A)
# ============================================================================

DOMAINS: Final[list[str]] = [
    "Medical",
    "HR",
    "Engineering",
    "Finance",
    "Legal",
    "Operations",
    "Sales",
    "Marketing",
    "General",  # Fallback for ambiguous documents
]

# Domain-specific vocabularies
# Each domain has allowed document types and topics
DOMAIN_VOCABULARIES: Final[dict[str, dict[str, list[str]]]] = {

    "Sales": {
        "document_types": ["Sales Manual", "Playbook", "Guideline"],
        "topics": [
            "prospecting", "cold_calling", "lead_generation",
            "sales_pipeline", "crm", "salesforce", "quota",
            "deal_closing", "negotiation", "pricing",
        ],
    },

    "Marketing": {
        "document_types": ["Marketing Plan", "Campaign Brief", "Guideline"],
        "topics": [
            "brand", "campaign", "content_marketing", "seo",
            "social_media", "email_marketing", "analytics",
            "lead_generation", "conversion", "roi",
        ],
    },

    "Medical": {
        "document_types": [
            "Medical Manual",
            "Clinical Report",
            "Research Paper",
            "Clinical Guideline",
            "Medical Reference",
        ],
        "topics": [
            # Anatomy
            "anatomy", "cardiovascular_system", "nervous_system", "respiratory_system",
            "digestive_system", "musculoskeletal_system",
            
            # Physiology
            "physiology", "homeostasis", "cellular_metabolism", "endocrine_regulation",
            
            # Pathology
            "pathology", "inflammation", "neoplasia", "cancer", "disease_mechanisms",
            
            # Pharmacology
            "pharmacology", "pharmacokinetics", "pharmacodynamics", "drug_interactions",
            "antibiotics", "antihypertensives", "analgesics",
            
            # Diagnostics
            "diagnostics", "laboratory_medicine", "medical_imaging", "x-ray", "ct_scan",
            "mri", "ultrasound", "pet_scan",
            
            # Diseases
            "infectious_diseases", "bacterial_infections", "viral_infections",
            "tuberculosis", "influenza", "hiv", "covid-19",
            
            # Public Health
            "public_health", "epidemiology", "disease_prevention", "vaccination",
            
            # Medical Ethics
            "medical_ethics", "bioethics", "patient_care", "informed_consent",
            
            # Emerging Tech
            "medical_ai", "genomic_medicine", "precision_medicine",
        ],
    },
    
    "HR": {
        "document_types": [
            "HR Policy",
            "Employee Handbook",
            "Guideline",
            "Memo",
        ],
        "topics": [
            # Leave & Time Off
            "annual_leave", "sick_leave", "parental_leave", "bereavement_leave",
            "unpaid_leave", "vacation_policy", "pto",
            
            # Work Arrangements
            "remote_work", "hybrid_work", "flexible_hours", "work_from_home",
            
            # Performance & Development
            "performance_review", "performance_evaluation", "career_development",
            "training", "professional_development",
            
            # Compensation & Benefits
            "compensation", "salary", "benefits", "health_insurance",
            "equity", "stock_options", "vesting", "401k", "retirement",
            
            # Conduct & Compliance
            "employee_conduct", "code_of_conduct", "harassment_policy",
            "diversity_inclusion", "workplace_safety",
            
            # Lifecycle
            "onboarding", "offboarding", "termination", "resignation",
            "probationary_period",
        ],
    },
    
    "Engineering": {
        "document_types": [
            "Technical Manual",
            "API Documentation",
            "System Architecture",
            "Standard Operating Procedure",
        ],
        "topics": [
            # Software Development
            "api_documentation", "system_architecture", "software_design",
            "coding_standards", "code_review", "git_workflow",
            
            # Infrastructure & DevOps
            "deployment", "ci_cd", "kubernetes", "docker", "containerization",
            "cloud_infrastructure", "aws", "azure", "gcp",
            
            # Data & Databases
            "database", "sql", "nosql", "data_modeling", "data_pipeline",
            
            # Security
            "security", "authentication", "authorization", "encryption",
            "vulnerability_management",
            
            # Operations
            "monitoring", "logging", "observability", "incident_response",
            "disaster_recovery", "performance_optimization",
            
            # Testing
            "testing", "unit_testing", "integration_testing", "test_automation",
        ],
    },
    
    "Finance": {
        "document_types": [
            "Financial Report",
            "Budget Document",
            "Procedure",
        ],
        "topics": [
            # Financial Planning
            "budget", "budgeting", "financial_planning", "forecasting",
            "cost_analysis",
            
            # Accounting
            "expenses", "revenue", "profit_loss", "balance_sheet",
            "cash_flow", "accounts_payable", "accounts_receivable",
            
            # Reporting
            "quarterly_report", "annual_report", "financial_statements",
            "audit", "compliance_reporting",
            
            # Operations
            "procurement", "vendor_management", "invoicing",
            "reimbursement", "travel_expenses", "expense_reports",
        ],
    },
    
    "Legal": {
        "document_types": [
            "Legal Document",
            "Contract",
            "Agreement",
        ],
        "topics": [
            # Contracts
            "contract", "agreement", "terms_of_service", "service_agreement",
            "nda", "non_disclosure",
            
            # Privacy & Data
            "privacy_policy", "data_protection", "gdpr", "ccpa",
            "data_privacy", "personal_data",
            
            # Intellectual Property
            "intellectual_property", "trademark", "copyright", "patent",
            "licensing",
            
            # Liability & Risk
            "liability", "indemnification", "insurance", "risk_management",
            
            # Compliance
            "compliance", "regulatory_compliance", "legal_compliance",
            "corporate_governance",
        ],
    },
    
    "Operations": {
        "document_types": [
            "Standard Operating Procedure",
            "Procedure",
            "Guideline",
        ],
        "topics": [
            # Process Management
            "standard_operating_procedure", "sop", "process_documentation",
            "workflow", "quality_assurance", "quality_control",
            
            # Supply Chain
            "supply_chain", "inventory", "logistics", "warehousing",
            "procurement",
            
            # Facilities
            "facilities", "office_management", "safety", "emergency_procedures",
            "security_procedures",
        ],
    },
    
    "General": {
        "document_types": [
            "Memo",
            "Announcement",
            "Other",
        ],
        "topics": [
            "general", "announcement", "communication", "update",
            "company_news", "miscellaneous",
        ],
    },
}

# ============================================================================
# Domain Helper Functions (NEW - Phase A)
# ============================================================================

def is_valid_domain(domain: str) -> bool:
    """Check if domain is in allowed list"""
    return domain in DOMAINS


def get_domain_for_document_type(doc_type: str) -> str | None:
    """
    Infer domain from document type.
    
    Args:
        doc_type: Document type string
        
    Returns:
        Domain name or None if not found
        
    Example:
        >>> get_domain_for_document_type("Medical Manual")
        "Medical"
    """
    for domain, vocab in DOMAIN_VOCABULARIES.items():
        if doc_type in vocab["document_types"]:
            return domain
    return None


def get_allowed_topics_for_domain(domain: str) -> list[str]:
    """
    Get list of allowed topics for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        List of allowed topic strings
        
    Example:
        >>> topics = get_allowed_topics_for_domain("Medical")
        >>> "anatomy" in topics
        True
    """
    return DOMAIN_VOCABULARIES.get(domain, {}).get("topics", [])


def get_allowed_document_types_for_domain(domain: str) -> list[str]:
    """
    Get list of allowed document types for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        List of allowed document type strings
    """
    return DOMAIN_VOCABULARIES.get(domain, {}).get("document_types", [])


def is_valid_topic_for_domain(topic: str, domain: str) -> bool:
    """
    Check if a topic is valid for a given domain.
    
    Args:
        topic: Topic string
        domain: Domain name
        
    Returns:
        True if topic is in domain's vocabulary
        
    Example:
        >>> is_valid_topic_for_domain("anatomy", "Medical")
        True
        >>> is_valid_topic_for_domain("annual_leave", "Medical")
        False
    """
    allowed = get_allowed_topics_for_domain(domain)
    return topic.lower() in [t.lower() for t in allowed]


def suggest_domain_from_topics(topics: list[str]) -> str:
    """
    Suggest domain based on topic overlap.
    
    Args:
        topics: List of topics
        
    Returns:
        Most likely domain based on topic matches
        
    Note:
        This is a fallback heuristic. Prefer LLM classification.
    """
    if not topics:
        return "General"
    
    # Count matches per domain
    domain_scores = {}
    for domain, vocab in DOMAIN_VOCABULARIES.items():
        allowed_topics = vocab["topics"]
        matches = sum(1 for t in topics if t.lower() in [a.lower() for a in allowed_topics])
        domain_scores[domain] = matches
    
    # Return domain with most matches
    best_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
    
    # If no matches, return General
    if domain_scores[best_domain] == 0:
        return "General"
    
    return best_domain


def validate_domain_consistency(
    domain: str,
    document_type: str,
    topics: list[str],
) -> list[str]:
    """
    Validate that domain, document_type, and topics are consistent.
    
    Args:
        domain: Domain string
        document_type: Document type string
        topics: List of topics
        
    Returns:
        List of validation error messages (empty if valid)
        
    Example:
        >>> errors = validate_domain_consistency(
        ...     "Medical",
        ...     "HR Policy",  # Wrong!
        ...     ["anatomy"]
        ... )
        >>> len(errors) > 0
        True
    """
    errors = []
    
    # Check domain is valid
    if not is_valid_domain(domain):
        errors.append(
            f"Invalid domain: {domain}. "
            f"Must be one of: {', '.join(DOMAINS)}"
        )
        return errors  # Can't proceed with invalid domain
    
    # Check document_type matches domain
    allowed_types = get_allowed_document_types_for_domain(domain)
    if document_type not in allowed_types:
        errors.append(
            f"Document type '{document_type}' is not valid for domain '{domain}'. "
            f"Allowed types: {', '.join(allowed_types)}"
        )
    
    # Check topics match domain
    allowed_topics = get_allowed_topics_for_domain(domain)
    invalid_topics = [t for t in topics if t.lower() not in [a.lower() for a in allowed_topics]]
    
    if invalid_topics:
        errors.append(
            f"Topics {invalid_topics} are not valid for domain '{domain}'. "
            f"Use topics from the {domain} vocabulary."
        )
    
    return errors

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
    # Existing exports
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
    
    # NEW - Phase A: Domain functions
    "DOMAINS",
    "DOMAIN_VOCABULARIES",
    "is_valid_domain",
    "get_domain_for_document_type",
    "get_allowed_topics_for_domain",
    "get_allowed_document_types_for_domain",
    "is_valid_topic_for_domain",
    "suggest_domain_from_topics",
    "validate_domain_consistency",
]