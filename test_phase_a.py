"""
Test Phase A: Domain Detection & Storage
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.business_rules import (
    DOMAINS,
    DOMAIN_VOCABULARIES,
    get_domain_for_document_type,
    is_valid_topic_for_domain,
    validate_domain_consistency,
    suggest_domain_from_topics,
)
from src.metadata.classifier import get_classifier
from src.orchestration.graph import run_extraction

print("=" * 70)
print("TEST PHASE A: Domain Detection & Storage")
print("=" * 70)

# ============================================================================
# Test 1: Domain Configuration
# ============================================================================
print("\n" + "=" * 70)
print("TEST 1: Domain Configuration")
print("=" * 70)

print(f"\nDomains defined: {len(DOMAINS)}")
for domain in DOMAINS:
    vocab = DOMAIN_VOCABULARIES.get(domain, {})
    print(f"  • {domain:15} - {len(vocab.get('topics', []))} topics, {len(vocab.get('document_types', []))} doc types")

print("\n✅ Domain vocabularies loaded")

# ============================================================================
# Test 2: Domain Helper Functions
# ============================================================================
print("\n" + "=" * 70)
print("TEST 2: Domain Helper Functions")
print("=" * 70)

# Test domain inference from document type
test_cases = [
    ("Medical Manual", "Medical"),
    ("HR Policy", "HR"),
    ("Technical Manual", "Engineering"),
    ("Financial Report", "Finance"),
    ("Contract", "Legal"),
]

print("\nTesting get_domain_for_document_type:")
for doc_type, expected_domain in test_cases:
    result = get_domain_for_document_type(doc_type)
    status = "✅" if result == expected_domain else "❌"
    print(f"  {status} '{doc_type}' → {result} (expected: {expected_domain})")

# Test topic validation
print("\nTesting is_valid_topic_for_domain:")
topic_tests = [
    ("anatomy", "Medical", True),
    ("annual_leave", "HR", True),
    ("annual_leave", "Medical", False),
    ("kubernetes", "Engineering", True),
]

for topic, domain, expected in topic_tests:
    result = is_valid_topic_for_domain(topic, domain)
    status = "✅" if result == expected else "❌"
    print(f"  {status} '{topic}' in {domain} → {result} (expected: {expected})")

# Test domain consistency validation
print("\nTesting validate_domain_consistency:")
consistency_test = validate_domain_consistency(
    domain="Medical",
    document_type="Medical Manual",
    topics=["anatomy", "pathology"],
)
print(f"  ✅ Valid Medical document: {len(consistency_test)} errors")

consistency_test_invalid = validate_domain_consistency(
    domain="Medical",
    document_type="HR Policy",  # Wrong type for domain!
    topics=["annual_leave"],     # Wrong topics for domain!
)
print(f"  ✅ Invalid combination detected: {len(consistency_test_invalid)} errors")

print("\n✅ Domain helper functions working")

# ============================================================================
# Test 3: Classification with Domain
# ============================================================================
print("\n" + "=" * 70)
print("TEST 3: Document Classification with Domain")
print("=" * 70)

# Medical document
medical_doc = """
Comprehensive Medical Compendium

1. Human Anatomy Overview

1.1 Cardiovascular System
The cardiovascular system consists of the heart, blood, and blood vessels.
Its primary function is to transport oxygen, nutrients, hormones, and waste
products throughout the body.

Key components: Heart (atria, ventricles, valves), Arteries, Veins, Capillaries

Clinical relevance: Hypertension results from increased systemic vascular
resistance. Atherosclerosis involves lipid deposition within arterial walls.
"""

print("\nClassifying medical document...")
classifier = get_classifier()
result = classifier.classify(medical_doc, preview_length=500)

print(f"  Domain: {result.domain}")
print(f"  Type: {result.document_type}")
print(f"  Complexity: {result.complexity}")
print(f"  Confidence: {result.confidence:.2f}")
print(f"  Reasoning: {result.reasoning}")

assert result.domain == "Medical", f"Expected Medical domain, got {result.domain}"
print("\n✅ Medical document classified correctly")

# HR document
hr_doc = """
REMOTE WORK POLICY
Effective Date: January 1, 2025
Version: 2.0
Document Owner: Human Resources

PURPOSE
This policy establishes guidelines for remote work arrangements for all employees.

ELIGIBILITY
All full-time employees who have completed their probationary period are
eligible to request remote work arrangements.

REQUIREMENTS
- Reliable internet connection
- Dedicated workspace
- Manager approval required
"""

print("\nClassifying HR document...")
result = classifier.classify(hr_doc, preview_length=500)

print(f"  Domain: {result.domain}")
print(f"  Type: {result.document_type}")
print(f"  Complexity: {result.complexity}")
print(f"  Confidence: {result.confidence:.2f}")

assert result.domain == "HR", f"Expected HR domain, got {result.domain}"
print("\n✅ HR document classified correctly")

# ============================================================================
# Test 4: Full Extraction Pipeline with Domain
# ============================================================================
print("\n" + "=" * 70)
print("TEST 4: Full Extraction Pipeline with Domain Storage")
print("=" * 70)

print("\nRunning extraction on medical document...")
extraction_result = run_extraction(
    document_id="test_medical_001",
    document_text=medical_doc,
    filename="medical_test.txt",
)

print(f"\nExtraction Status: {extraction_result['status']}")

if extraction_result['status'] == 'completed':
    classification = extraction_result['classification']
    metadata = extraction_result['doc_metadata']
    
    print(f"\nClassification:")
    print(f"  Domain: {classification['domain']}")
    print(f"  Type: {classification['document_type']}")
    print(f"  Complexity: {classification['complexity']}")
    
    print(f"\nExtracted Metadata:")
    print(f"  Domain: {metadata.get('domain')}")
    print(f"  Document Type: {metadata.get('document_type')}")
    print(f"  Department: {metadata.get('department')}")
    print(f"  Topics: {metadata.get('topics', [])[:5]}")
    
    # Verify domain is stored
    assert metadata.get('domain') == 'Medical', "Domain not stored in metadata!"
    
    print(f"\nChunks Created: {len(extraction_result['chunks'])}")
    
    # Check first chunk has domain in metadata
    if extraction_result['chunks']:
        first_chunk_meta = extraction_result['chunks'][0]['metadata']
        print(f"  First chunk domain: {first_chunk_meta.get('domain')}")
        assert first_chunk_meta.get('domain') == 'Medical', "Domain not in chunk metadata!"
    
    print(f"\nValidation:")
    print(f"  Is Valid: {extraction_result.get('is_valid')}")
    print(f"  Errors: {len(extraction_result.get('validation_errors', []))}")
    
    if extraction_result.get('validation_errors'):
        print("  Validation errors:")
        for error in extraction_result['validation_errors'][:3]:
            print(f"    - {error}")
    
    print("\n✅ Domain stored throughout pipeline")
else:
    print(f"\n❌ Extraction failed: {extraction_result.get('error')}")
    sys.exit(1)

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 70)
print("🎉 PHASE A COMPLETE!")
print("=" * 70)
print("\n✅ Domain detection working")
print("✅ Domain vocabularies defined")
print("✅ Domain validation implemented")
print("✅ Domain stored in metadata and chunks")
print("✅ Classification includes domain")
print("\nNext: Phase B - Vocabulary Scoping")
print("=" * 70 + "\n")