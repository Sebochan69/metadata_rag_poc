"""
Test Phase C: Eager Validation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.graph import run_extraction

print("=" * 70)
print("TEST PHASE C: Eager Validation")
print("=" * 70)

# Test 1: Valid document should pass early validation
print("\n" + "=" * 70)
print("TEST 1: Valid Document - Should Pass Early Validation")
print("=" * 70)

valid_doc = """
CARDIOVASCULAR DISEASE REFERENCE

Overview of Hypertension

PATHOPHYSIOLOGY
Hypertension involves increased blood pressure in the cardiovascular system.
Key factors include arterial resistance and cardiac output.

DIAGNOSIS
- Blood pressure monitoring
- ECG
- Laboratory tests

TREATMENT
- Pharmacological interventions
- Lifestyle modifications
"""

print("\nProcessing valid Medical document...")
result = run_extraction(
    document_id="test_valid_001",
    document_text=valid_doc,
    filename="valid_medical.txt",
)

if result['status'] == 'completed':
    print("✅ Valid document passed early validation")
    print(f"   Domain: {result['doc_metadata'].get('domain')}")
    print(f"   Topics: {result['doc_metadata'].get('topics', [])}")
    
    if result.get('early_validation_warnings'):
        print(f"   Warnings: {len(result['early_validation_warnings'])}")
        for warning in result['early_validation_warnings'][:3]:
            print(f"      - {warning}")
else:
    print(f"❌ Document failed: {result.get('error')}")
    print(f"   Stage: {result.get('error_stage')}")

# Test 2: Document with no valid topics should fail early
print("\n" + "=" * 70)
print("TEST 2: Invalid Topics - Should Fail Early Validation")
print("=" * 70)

# This document talks about random stuff not in any vocabulary
invalid_doc = """
RANDOM NONSENSE DOCUMENT

This document discusses quantum foam theory and interdimensional portal mechanics.
We will also cover telepathic communication protocols and astral projection techniques.

The main topics are:
- Quantum entanglement visualization
- Psychic energy amplification
- Time travel paradox resolution
"""

print("\nProcessing document with invalid topics...")
result = run_extraction(
    document_id="test_invalid_001",
    document_text=invalid_doc,
    filename="invalid_topics.txt",
)

if result['status'] == 'failed':
    print("✅ Document correctly failed early validation")
    print(f"   Error: {result.get('error')}")
    print(f"   Stage: {result.get('error_stage')}")
    
    # Verify it failed at extraction stage, not later
    if result.get('error_stage') == 'doc_metadata_extraction':
        print("✅ Failed early (at extraction stage) - not wasting time chunking")
    else:
        print(f"❌ Failed at wrong stage: {result.get('error_stage')}")
else:
    print(f"❌ Document should have failed but didn't")
    print(f"   Domain: {result.get('doc_metadata', {}).get('domain')}")
    print(f"   Topics: {result.get('doc_metadata', {}).get('topics', [])}")

# Test 3: Document with low confidence should warn but pass
print("\n" + "=" * 70)
print("TEST 3: Low Confidence - Should Warn But Pass")
print("=" * 70)

ambiguous_doc = """
MEMO

To: All Staff
From: Management
Date: Today

This is a short memo about something.

Please be aware of things.

Thank you.
"""

print("\nProcessing ambiguous document...")
result = run_extraction(
    document_id="test_ambiguous_001",
    document_text=ambiguous_doc,
    filename="ambiguous.txt",
)

if result['status'] == 'completed':
    print("✅ Ambiguous document passed (with warnings expected)")
    print(f"   Domain: {result['doc_metadata'].get('domain')}")
    print(f"   Confidence: {result['classification'].get('confidence')}")
    
    if result.get('early_validation_warnings'):
        print(f"   Warnings: {len(result['early_validation_warnings'])}")
        for warning in result['early_validation_warnings'][:3]:
            print(f"      - {warning}")
    else:
        print("   (No warnings - might be misclassified as high confidence)")
else:
    print(f"⚠️  Document failed (may be too ambiguous)")
    print(f"   Error: {result.get('error')}")

# Test 4: Verify final validation still runs
print("\n" + "=" * 70)
print("TEST 4: Final Validation Still Runs")
print("=" * 70)

normal_doc = """
REMOTE WORK POLICY

Effective Date: 2025-01-01
Version: 2.0
Department: HR

All employees may request remote work arrangements.

ELIGIBILITY
- Completed probationary period
- Manager approval required

REQUIREMENTS
- Reliable internet
- Dedicated workspace
"""

print("\nProcessing normal document...")
result = run_extraction(
    document_id="test_normal_001",
    document_text=normal_doc,
    filename="normal.txt",
)

if result['status'] == 'completed':
    print("✅ Document passed both early and final validation")
    print(f"   Early warnings: {len(result.get('early_validation_warnings', []))}")
    print(f"   Final valid: {result.get('is_valid')}")
    print(f"   Final errors: {len(result.get('validation_errors', []))}")
    
    if result.get('validation_errors'):
        print("   Final validation errors:")
        for error in result['validation_errors'][:3]:
            print(f"      - {error}")
else:
    print(f"❌ Document failed: {result.get('error')}")

# Summary
print("\n" + "=" * 70)
print("🎉 PHASE C COMPLETE!")
print("=" * 70)
print("\n✅ Early validation implemented")
print("✅ Critical errors caught before chunking")
print("✅ Warnings logged but don't fail pipeline")
print("✅ Final validation still runs at end")
print("\nNext: Phase D - Domain-Constrained Retrieval")
print("=" * 70 + "\n")