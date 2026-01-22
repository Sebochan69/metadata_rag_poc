"""
Quick test: Verify retrieval works with medical chunks.
Tests the stress test queries from the medical document.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.retrieval.retriever import get_retriever
from src.generation.answer_generator import get_answer_generator

print("=" * 70)
print("QUICK RETRIEVAL TEST")
print("=" * 70)

retriever = get_retriever()
generator = get_answer_generator()

# Stress test queries from medical document
test_queries = [
    "Which hormone affects blood glucose?",
    "Which disease involves dopaminergic neurons?",
    "Which imaging modality uses magnetic fields?",
    "What are the cardinal signs of inflammation?",
]

print(f"\nTesting {len(test_queries)} queries...")

for i, query in enumerate(test_queries, 1):
    print("\n" + "=" * 70)
    print(f"QUERY {i}: {query}")
    print("=" * 70)
    
    # Retrieve
    try:
        result = retriever.retrieve(query, top_k=3)
        
        print(f"\n📊 Retrieval:")
        print(f"   Reformulated: {result.reformulated_query}")
        print(f"   Results found: {result.total_results}")
        
        if result.chunks:
            print(f"   Top result score: {result.chunks[0]['score']:.2%}")
            print(f"   Text preview: {result.chunks[0]['text'][:150]}...")
            
            # Generate answer
            print(f"\n💬 Generating answer...")
            answer = generator.generate(query, result)
            
            print(f"\n📝 Answer:")
            print(f"   {answer.answer}")
            print(f"\n   Confidence: {answer.confidence:.0%}")
            print(f"   Sources: {answer.context_used} chunks")
        else:
            print("   ❌ No results found!")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nNext steps based on results:")
print("  ✅ If answers are good → Skip theoretical Q&A, move to Medical-only enforcement")
print("  ⚠️  If answers are weak → Implement theoretical Q&A (Priority 3)")
print("  ❌ If retrieval fails → Debug retrieval/embedding issues")
print("=" * 70 + "\n")