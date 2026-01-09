"""
Ingest the medical RAG stress test document.
This is a comprehensive medical compendium designed to test:
- Chunking strategy
- Cross-section retrieval
- Medical terminology handling
- Long-range semantic queries
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.graph import run_extraction
from src.storage.qdrant_manager import get_qdrant_manager

print("=" * 70)
print("INGESTING: Medical RAG Stress Test Document")
print("=" * 70)

# Load the medical document
medical_file = Path("data/raw/medical_rag_stress_test.txt")

if not medical_file.exists():
    print(f"\n❌ File not found: {medical_file}")
    print("Please ensure medical_rag_stress_test.txt exists in data/raw/")
    sys.exit(1)

print(f"\nLoading document from: {medical_file}")
with open(medical_file, 'r', encoding='utf-8') as f:
    medical_text = f.read()

print(f"Document size: {len(medical_text)} characters")
print(f"Estimated words: {len(medical_text.split())}")

# Extract metadata and chunk
print("\nExtracting metadata and chunking...")
result = run_extraction(
    document_id="medical_compendium_stress_test",
    document_text=medical_text,
    filename="medical_rag_stress_test.txt",
)

if result['status'] != 'completed':
    print(f"\n❌ Extraction failed: {result.get('error')}")
    sys.exit(1)

# Show results
classification = result['classification']
metadata = result['doc_metadata']
chunks = result['chunks']

print("\n" + "=" * 70)
print("EXTRACTION RESULTS")
print("=" * 70)

print(f"\nClassification:")
print(f"  Domain: {classification['domain']}")
print(f"  Type: {classification['document_type']}")
print(f"  Complexity: {classification['complexity']}")
print(f"  Confidence: {classification['confidence']:.2f}")

print(f"\nMetadata:")
print(f"  Domain: {metadata['domain']}")
print(f"  Topics ({len(metadata['topics'])}): {metadata['topics'][:5]}...")
print(f"  Department: {metadata.get('department')}")
print(f"  Authority: {metadata.get('authority_level')}")

print(f"\nChunking:")
print(f"  Total chunks: {len(chunks)}")
print(f"  Average chunk size: {sum(len(c['text']) for c in chunks) // len(chunks)} chars")

# Store in Qdrant
print("\nStoring chunks in Qdrant...")
qdrant = get_qdrant_manager()
qdrant.add_chunks(chunks, 'medical_compendium_stress_test')

stats = qdrant.get_collection_stats()

print("\n" + "=" * 70)
print("✅ MEDICAL STRESS TEST DOCUMENT INGESTED")
print("=" * 70)
print(f"Total chunks in database: {stats['total_chunks']}")
print(f"Chunks from this document: {len(chunks)}")
print("\nReady for stress testing!")
print("=" * 70 + "\n")