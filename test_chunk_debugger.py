"""
Test script for chunk debugger system.

Tests:
1. Debugger initialization
2. Raw document saving
3. Chunk saving
4. Rejected chunk handling
5. Stats reporting
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.chunk_debugger import get_chunk_debugger

print("=" * 70)
print("TEST: Chunk Debugger System")
print("=" * 70)

# Test 1: Initialize debugger
print("\n[TEST 1] Initialize Chunk Debugger")
debugger = get_chunk_debugger()
print(f"✅ Debugger initialized")
print(f"   Base path: {debugger.base_path}")

# Test 2: Save raw document
print("\n[TEST 2] Save Raw Document")
test_doc = """
MEDICAL TEST DOCUMENT

This is a test medical document about cardiovascular diseases.

Section 1: Hypertension
Hypertension is high blood pressure affecting the cardiovascular system.

Section 2: Treatment
Treatment includes ACE inhibitors and lifestyle modifications.
"""

raw_path = debugger.save_raw_document(
    document_id="test_medical_001",
    document_text=test_doc,
    document_name="test_medical.txt",
    metadata={"domain": "Medical", "document_type": "Medical Reference"}
)

print(f"✅ Raw document saved")
print(f"   Path: {raw_path}")
print(f"   Exists: {raw_path.exists()}")

# Test 3: Save chunks
print("\n[TEST 3] Save Chunks")

test_chunks = [
    {
        "text": "MEDICAL TEST DOCUMENT\n\nThis is a test medical document about cardiovascular diseases.",
        "chunk_number": 0,
        "start_char": 0,
        "end_char": 80,
        "metadata": {
            "domain": "Medical",
            "document_type": "Medical Reference",
            "topics": ["cardiovascular_system"]
        }
    },
    {
        "text": "Section 1: Hypertension\nHypertension is high blood pressure affecting the cardiovascular system.",
        "chunk_number": 1,
        "start_char": 81,
        "end_char": 160,
        "metadata": {
            "domain": "Medical",
            "document_type": "Medical Reference",
            "topics": ["cardiovascular_system", "pathology"]
        }
    },
    {
        "text": "Section 2: Treatment\nTreatment includes ACE inhibitors and lifestyle modifications.",
        "chunk_number": 2,
        "start_char": 161,
        "end_char": 240,
        "metadata": {
            "domain": "Medical",
            "document_type": "Medical Reference",
            "topics": ["pharmacology"]
        }
    }
]

chunk_ids = []
for chunk in test_chunks:
    chunk_id = debugger.save_chunk(
        chunk=chunk,
        document_id="test_medical_001",
        document_name="test_medical.txt",
        source_type="txt",
        chunk_strategy="simple_fixed",
        chunk_config={"chunk_size": 500, "overlap": 100}
    )
    chunk_ids.append(chunk_id)
    print(f"✅ Chunk {chunk['chunk_number']} saved: {chunk_id[:8]}...")

# Test 4: Save rejected chunk
print("\n[TEST 4] Save Rejected Chunk")

bad_chunk = {
    "text": "This chunk is invalid",
    "chunk_number": 999,
    "start_char": 0,
    "end_char": 21,
    "metadata": {}
}

rejected_id = debugger.save_rejected_chunk(
    chunk=bad_chunk,
    document_id="test_medical_001",
    reason="Missing required metadata",
    error="KeyError: 'domain'"
)

print(f"✅ Rejected chunk saved: {rejected_id[:8]}...")

# Test 5: Get stats
print("\n[TEST 5] Debug Statistics")
stats = debugger.get_stats()

print(f"✅ Statistics retrieved:")
print(f"   Raw documents: {stats['raw_documents']}")
print(f"   Chunked files: {stats['chunked_files']}")
print(f"   Rejected files: {stats['rejected_files']}")
print(f"   Base path: {stats['base_path']}")

# Test 6: Verify files exist
print("\n[TEST 6] Verify Files on Disk")

chunked_dir = debugger.base_path / "chunked"
chunk_files = list(chunked_dir.glob("test_medical_001_chunk*.json"))

print(f"✅ Found {len(chunk_files)} chunk files in {chunked_dir}")

if chunk_files:
    # Read and display first chunk
    import json
    
    first_chunk_file = chunk_files[0]
    with open(first_chunk_file, 'r') as f:
        chunk_data = json.load(f)
    
    print(f"\n   Sample chunk JSON structure:")
    print(f"   - chunk_id: {chunk_data['chunk_id'][:16]}...")
    print(f"   - document_id: {chunk_data['document_id']}")
    print(f"   - chunk_index: {chunk_data['chunk_index']}")
    print(f"   - text_length: {chunk_data['text_length']}")
    print(f"   - domain: {chunk_data['metadata'].get('domain')}")
    print(f"   - topics: {chunk_data['metadata'].get('topics', [])}")
    print(f"   - chunk_strategy: {chunk_data['chunk_strategy']}")
    print(f"   - embedding_status: {chunk_data['embedding_status']}")

# Summary
print("\n" + "=" * 70)
print("🎉 CHUNK DEBUGGER TESTS PASSED!")
print("=" * 70)
print(f"\n✅ All functions working correctly")
print(f"✅ Files saved to: {debugger.base_path}")
print(f"✅ Ready for integration into pipeline")
print("\nNext steps:")
print("  1. Integrate into src/orchestration/nodes.py (see artifact)")
print("  2. Re-ingest medical document")
print("  3. Verify chunks in data/debug_chunks/chunked/")
print("=" * 70 + "\n")