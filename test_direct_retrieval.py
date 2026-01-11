"""
Test if chunks are actually retrievable (bypass query understanding).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.storage.qdrant_manager import get_qdrant_manager
from src.storage.embedder import get_embedder
from qdrant_client.models import Filter, FieldCondition, MatchValue

print("=" * 70)
print("DIAGNOSTIC: Direct Retrieval Test (Bypass Query Understanding)")
print("=" * 70)

qdrant = get_qdrant_manager()
embedder = get_embedder()

# Test 1: Check Medical chunks exist in DB
print("\n[TEST 1] Checking for Medical domain chunks...")
result = qdrant.client.scroll(
    collection_name="company_docs",
    scroll_filter=Filter(
        must=[FieldCondition(key="domain", match=MatchValue(value="Medical"))]
    ),
    limit=10
)

medical_chunks = result[0]
print(f"✓ Found {len(medical_chunks)} Medical chunks in database")

if medical_chunks:
    print("\nFirst Medical chunk:")
    print(f"  ID: {medical_chunks[0].id}")
    print(f"  Domain: {medical_chunks[0].payload.get('domain')}")
    print(f"  Topics: {medical_chunks[0].payload.get('topics', [])[:5]}")
    print(f"  Text preview: {medical_chunks[0].payload.get('text', '')[:200]}...")
else:
    print("❌ NO MEDICAL CHUNKS FOUND! Ingestion failed.")
    sys.exit(1)

# Test 2: Direct vector search for "insulin glucose"
print("\n[TEST 2] Direct vector search: 'insulin glucose hormone'")
query_vec = embedder.embed_single("insulin glucose hormone")

search_results = qdrant.client.search(
    collection_name="company_docs",
    query_vector=query_vec,
    limit=5
)

print(f"✓ Found {len(search_results)} results")

for i, hit in enumerate(search_results, 1):
    print(f"\n  Result {i}:")
    print(f"    Score: {hit.score:.3f}")
    print(f"    Domain: {hit.payload.get('domain')}")
    print(f"    Text: {hit.payload.get('text', '')[:150]}...")

# Test 3: Search WITH domain filter
print("\n[TEST 3] Vector search WITH Medical domain filter")
search_with_filter = qdrant.client.search(
    collection_name="company_docs",
    query_vector=query_vec,
    query_filter=Filter(
        must=[FieldCondition(key="domain", match=MatchValue(value="Medical"))]
    ),
    limit=5
)

print(f"✓ Found {len(search_with_filter)} results with domain filter")

for i, hit in enumerate(search_with_filter, 1):
    print(f"\n  Result {i}:")
    print(f"    Score: {hit.score:.3f}")
    print(f"    Domain: {hit.payload.get('domain')}")
    print(f"    Text: {hit.payload.get('text', '')[:150]}...")

# Test 4: Test the retriever with query understanding DISABLED
print("\n[TEST 4] Using Retriever class (query understanding OFF)")
from src.retrieval.retriever import get_retriever

retriever = get_retriever()

# Monkey-patch to disable query understanding temporarily
result = retriever.retrieve(
    "insulin glucose hormone",
    top_k=5,
    use_query_understanding=False  # KEY: BYPASS BROKEN PART
)

print(f"✓ Retriever found {result.total_results} results")

if result.chunks:
    print(f"\n  Top result:")
    print(f"    Score: {result.chunks[0]['score']:.3f}")
    print(f"    Domain: {result.chunks[0]['metadata'].get('domain')}")
    print(f"    Text: {result.chunks[0]['text'][:150]}...")
else:
    print("❌ Retriever returned 0 results even with query understanding OFF!")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)