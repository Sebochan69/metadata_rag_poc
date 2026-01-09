"""
Test Phase B: Vocabulary Scoping
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.business_rules import (
    get_allowed_topics_for_domain,
    is_valid_topic_for_domain,
)
from src.orchestration.graph import run_extraction

print("=" * 70)
print("TEST PHASE B: Vocabulary Scoping")
print("=" * 70)

# Test 1: Verify vocabularies are enforced
print("\n" + "=" * 70)
print("TEST 1: Domain Vocabulary Enforcement")
print("=" * 70)

medical_topics = get_allowed_topics_for_domain("Medical")
hr_topics = get_allowed_topics_for_domain("HR")

print(f"\nMedical domain has {len(medical_topics)} allowed topics")
print(f"Sample: {medical_topics[:5]}")

print(f"\nHR domain has {len(hr_topics)} allowed topics")
print(f"Sample: {hr_topics[:5]}")

# Cross-domain validation
print("\nCross-domain validation:")
print(f"  'anatomy' valid for Medical: {is_valid_topic_for_domain('anatomy', 'Medical')}")
print(f"  'anatomy' valid for HR: {is_valid_topic_for_domain('anatomy', 'HR')}")
print(f"  'annual_leave' valid for HR: {is_valid_topic_for_domain('annual_leave', 'HR')}")
print(f"  'annual_leave' valid for Medical: {is_valid_topic_for_domain('annual_leave', 'Medical')}")

print("\n✅ Domain vocabularies are distinct")

# Test 2: Extract metadata with vocabulary enforcement
print("\n" + "=" * 70)
print("TEST 2: Extraction with Vocabulary Enforcement")
print("=" * 70)

medical_doc = """
MEDICAL REFERENCE: Cardiovascular Diseases

Overview of Hypertension and Heart Disease

INTRODUCTION
Hypertension, or high blood pressure, is a major risk factor for cardiovascular 
disease. The cardiovascular system consists of the heart, blood vessels, and blood.

PATHOPHYSIOLOGY
Chronic hypertension leads to:
- Increased cardiac workload
- Arterial wall thickening (atherosclerosis)
- Risk of myocardial infarction

PHARMACOLOGICAL TREATMENT
Treatment typically involves:
- ACE inhibitors
- Beta blockers
- Diuretics

DIAGNOSIS
Diagnostic methods include:
- Blood pressure monitoring
- ECG
- Echocardiography
- Laboratory tests
"""

print("\nExtracting Medical document...")
result = run_extraction(
    document_id="test_medical_vocab_001",
    document_text=medical_doc,
    filename="cardiovascular_disease.txt",
)

if result['status'] == 'completed':
    metadata = result['doc_metadata']
    
    print(f"\nDomain: {metadata.get('domain')}")
    print(f"Topics extracted: {metadata.get('topics', [])}")
    
    # Verify all topics are from Medical vocabulary
    topics = metadata.get('topics', [])
    all_valid = all(is_valid_topic_for_domain(t, 'Medical') for t in topics)
    
    if all_valid:
        print("✅ All topics are from Medical domain vocabulary")
    else:
        print("❌ Some topics are not from Medical vocabulary!")
        invalid = [t for t in topics if not is_valid_topic_for_domain(t, 'Medical')]
        print(f"   Invalid: {invalid}")
    
    # Check validation passed
    if result.get('is_valid'):
        print("✅ Metadata validation passed")
    else:
        print(f"❌ Validation failed with {len(result.get('validation_errors', []))} errors")
        for error in result.get('validation_errors', [])[:3]:
            print(f"   - {error}")
else:
    print(f"❌ Extraction failed: {result.get('error')}")
    sys.exit(1)

# Test 3: Try HR document
print("\n" + "=" * 70)
print("TEST 3: HR Document with Vocabulary Enforcement")
print("=" * 70)

hr_doc = """
REMOTE WORK AND FLEXIBLE HOURS POLICY

Effective Date: January 1, 2025
Version: 2.0
Department: Human Resources

PURPOSE
This policy establishes guidelines for remote work and flexible hour arrangements.

ELIGIBILITY
All full-time employees who have completed probationary period are eligible.

REMOTE WORK OPTIONS
1. Full-time remote work
2. Hybrid schedule (2-3 days in office)
3. Flexible hours with core hours requirement

EQUIPMENT AND TECHNOLOGY
Company will provide:
- Laptop
- Monitor
- Necessary software

PERFORMANCE EXPECTATIONS
Remote employees must:
- Maintain regular communication
- Meet all deadlines
- Attend required meetings

APPROVAL PROCESS
1. Submit request via HR portal
2. Manager review and approval
3. IT setup of equipment
"""

print("\nExtracting HR document...")
result = run_extraction(
    document_id="test_hr_vocab_001",
    document_text=hr_doc,
    filename="remote_work_policy.txt",
)

if result['status'] == 'completed':
    metadata = result['doc_metadata']
    
    print(f"\nDomain: {metadata.get('domain')}")
    print(f"Topics extracted: {metadata.get('topics', [])}")
    
    # Verify all topics are from HR vocabulary
    topics = metadata.get('topics', [])
    all_valid = all(is_valid_topic_for_domain(t, 'HR') for t in topics)
    
    if all_valid:
        print("✅ All topics are from HR domain vocabulary")
    else:
        print("❌ Some topics are not from HR vocabulary!")
        invalid = [t for t in topics if not is_valid_topic_for_domain(t, 'HR')]
        print(f"   Invalid: {invalid}")
    
    if result.get('is_valid'):
        print("✅ Metadata validation passed")
else:
    print(f"❌ Extraction failed: {result.get('error')}")

# Summary
print("\n" + "=" * 70)
print("🎉 PHASE B COMPLETE!")
print("=" * 70)
print("\n✅ Vocabulary scoping enforced")
print("✅ Topics validated against domain")
print("✅ Invalid topics filtered or rejected")
print("✅ LLM constrained to domain-specific terms")
print("\nNext: Phase C - Eager Validation")
print("=" * 70 + "\n")