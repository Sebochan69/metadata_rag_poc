from src.orchestration.graph import run_extraction
from src.storage.chroma_manager import get_chroma_manager
from src.retrieval.retriever import get_retriever

print("=" * 60)
print("TEST: Phase 5 - Storage & Retrieval")
print("=" * 60)

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

# Step 1: Extract metadata and chunks
print("\n1. Extracting metadata...")
result = run_extraction(
    document_id="remote_work_001",
    document_text=sample_doc,
)

if result['status'] != 'completed':
    print(f"❌ Extraction failed: {result.get('error')}")
    exit(1)

print(f"✅ Metadata extracted")
print(f"   Chunks: {len(result['chunks'])}")

# Step 2: Store in ChromaDB
print("\n2. Storing in ChromaDB...")
chroma = get_chroma_manager()
chroma.add_chunks(result['chunks'], result['document_id'])
print(f"✅ Stored in vector database")
print(f"   Collection stats: {chroma.get_collection_stats()}")

# Step 3: Test retrieval
print("\n3. Testing retrieval...")
retriever = get_retriever()

queries = [
    "How do I apply for remote work?",
    "What are the requirements for working from home?",
    "Who is eligible for remote work?",
]

for query in queries:
    print(f"\n   Query: {query}")
    query_result = retriever.retrieve(query, top_k=3)
    print(f"   Intent: {query_result.intent}")
    print(f"   Results: {query_result.total_results}")
    if query_result.chunks:
        print(f"   Top result score: {query_result.chunks[0]['score']:.3f}")

print("\n" + "=" * 60)
print("🎉 Phase 5 complete! Storage & Retrieval working!")
print("=" * 60)