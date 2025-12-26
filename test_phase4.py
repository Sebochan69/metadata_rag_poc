from src.orchestration.graph import run_extraction

# Sample document
sample_doc = """
REMOTE WORK POLICY
Effective Date: January 1, 2025
Version: 2.0
Department: Human Resources

This policy establishes guidelines for remote work arrangements.

ELIGIBILITY
All full-time employees who have completed their probationary period
are eligible to request remote work arrangements.

REQUIREMENTS
- Reliable internet connection
- Dedicated workspace
- Manager approval required

APPROVAL PROCESS
1. Submit request to manager
2. Manager reviews and approves
3. HR confirms eligibility
"""

print("=" * 60)
print("TEST: Full Metadata Extraction Pipeline")
print("=" * 60)

# Run extraction
result = run_extraction(
    document_id="test_doc_001",
    document_text=sample_doc,
    filename="remote_work_policy.txt",
)

print(f"\nStatus: {result['status']}")
print(f"\nClassification:")
print(f"  Type: {result.get('classification', {}).get('document_type')}")
print(f"  Complexity: {result.get('classification', {}).get('complexity')}")
print(f"  Confidence: {result.get('classification', {}).get('confidence')}")

print(f"\nExtracted Metadata:")
metadata = result.get('doc_metadata', {})
print(f"  Document Type: {metadata.get('document_type')}")
print(f"  Department: {metadata.get('department')}")
print(f"  Authority Level: {metadata.get('authority_level')}")
print(f"  Topics: {metadata.get('topics')}")
print(f"  Intended Audience: {metadata.get('intended_audience')}")
print(f"  Effective Date: {metadata.get('effective_date')}")
print(f"  Version: {metadata.get('version')}")

print(f"\nChunking:")
print(f"  Chunks Created: {len(result.get('chunks', []))}")

print(f"\nValidation:")
print(f"  Is Valid: {result.get('is_valid')}")
print(f"  Errors: {len(result.get('validation_errors', []))}")
if result.get('validation_errors'):
    for error in result['validation_errors'][:3]:
        print(f"    - {error}")

print(f"\nPerformance:")
print(f"  Processing Time: {result.get('processing_time', 0):.2f}s")
print(f"  Tokens Used: {result.get('tokens_used', 0)}")
print(f"  Estimated Cost: ${result.get('estimated_cost', 0):.4f}")

print("\n" + "=" * 60)
if result['status'] == 'completed':
    print("🎉 Full pipeline working!")
else:
    print(f"❌ Pipeline failed: {result.get('error')}")
print("=" * 60)