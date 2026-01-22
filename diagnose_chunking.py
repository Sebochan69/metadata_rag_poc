"""
Diagnostic script to check why we only got 4 chunks.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.chunker import chunk_document
import tiktoken

print("=" * 70)
print("DIAGNOSTIC: Chunking Issue")
print("=" * 70)

# Load medical document
medical_file = Path("data/raw/medical_rag_stress_test.txt")

with open(medical_file, 'r', encoding='utf-8') as f:
    medical_text = f.read()

print(f"\n📄 Document Stats:")
print(f"   Characters: {len(medical_text)}")
print(f"   Words: {len(medical_text.split())}")

# Count tokens
encoding = tiktoken.get_encoding("cl100k_base")
tokens = encoding.encode(medical_text)
print(f"   Tokens (tiktoken): {len(tokens)}")

# Expected chunks
expected_chunks = len(tokens) // 500
print(f"   Expected chunks (500 tokens/chunk): ~{expected_chunks}")

# Actually chunk it
print(f"\n🔪 Chunking with current settings...")
chunks = chunk_document(
    text=medical_text,
    chunk_size=500,
    chunk_overlap=100,
    document_metadata={"domain": "Medical"}
)

print(f"   ✅ Created {len(chunks)} chunks")

# Analyze chunks
print(f"\n📊 Chunk Analysis:")
for i, chunk in enumerate(chunks):
    chunk_tokens = encoding.encode(chunk['text'])
    print(f"\n   Chunk {i}:")
    print(f"      Characters: {len(chunk['text'])}")
    print(f"      Words: {len(chunk['text'].split())}")
    print(f"      Tokens: {len(chunk_tokens)}")
    print(f"      Start: {chunk['start_char']}")
    print(f"      End: {chunk['end_char']}")
    print(f"      Text preview: {chunk['text'][:80]}...")

# Check debug output
print(f"\n🔍 Debug Output Check:")
debug_dir = Path("data/debug_chunks/chunked")
if debug_dir.exists():
    chunk_files = list(debug_dir.glob("medical_*.json"))
    print(f"   Found {len(chunk_files)} JSON files in debug output")
    
    if chunk_files:
        # Check first file
        with open(chunk_files[0], 'r') as f:
            chunk_data = json.load(f)
        
        print(f"\n   First chunk from JSON:")
        print(f"      chunk_index: {chunk_data['chunk_index']}")
        print(f"      text_length: {chunk_data['text_length']}")
        print(f"      word_count: {chunk_data['word_count']}")
        print(f"      chunk_config: {chunk_data['chunk_config']}")
else:
    print(f"   ⚠️  Debug directory not found")

# Check Qdrant
print(f"\n💾 Qdrant Storage Check:")
try:
    from src.storage.qdrant_manager import get_qdrant_manager
    
    qdrant = get_qdrant_manager()
    
    # Scroll to get all chunks for this document
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    result = qdrant.client.scroll(
        collection_name="company_docs",
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value="medical_compendium_stress_test")
                )
            ]
        ),
        limit=100
    )
    
    stored_chunks = result[0]
    print(f"   Chunks in Qdrant: {len(stored_chunks)}")
    
    if stored_chunks:
        print(f"\n   First stored chunk:")
        first = stored_chunks[0]
        print(f"      ID: {first.id}")
        print(f"      chunk_number: {first.payload.get('chunk_number')}")
        print(f"      text_length: {len(first.payload.get('text', ''))}")
        print(f"      domain: {first.payload.get('domain')}")
        
except Exception as e:
    print(f"   ⚠️  Qdrant check failed: {e}")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
print("\nPlease share the output above!")
print("=" * 70 + "\n")