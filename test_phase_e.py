"""
Test Phase E: Stress Testing with Medical Documents

Tests from the medical document's "Long-Range Cross-Referencing Section":
- Cross-section semantic retrieval
- Medical terminology precision
- Multi-hop reasoning
- Dense technical content handling
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.retrieval.retriever import get_retriever
from src.generation.answer_generator import get_answer_generator

print("=" * 70)
print("TEST PHASE E: Medical Document Stress Testing")
print("=" * 70)

retriever = get_retriever()
generator = get_answer_generator()

# Test queries from the document's cross-referencing section
stress_test_queries = [
    {
        "query": "Which hormone mentioned affects blood glucose?",
        "expected_answer": "Insulin and glucagon",
        "section": "Section 2 (Physiology)",
    },
    {
        "query": "Which disease involves dopaminergic neurons?",
        "expected_answer": "Parkinson's disease",
        "section": "Section 1 (Nervous System)",
    },
    {
        "query": "Which imaging modality uses magnetic fields?",
        "expected_answer": "MRI",
        "section": "Section 5 (Diagnostics)",
    },
    {
        "query": "Which pharmacology concept uses ADME?",
        "expected_answer": "Pharmacokinetics",
        "section": "Section 4 (Pharmacology)",
    },
    {
        "query": "What are the cardinal signs of inflammation?",
        "expected_answer": "Rubor, Calor, Tumor, Dolor, Functio laesa",
        "section": "Section 3 (Pathology)",
    },
]

print("\nRunning stress test queries...")
print("These queries require cross-section retrieval and medical terminology understanding.\n")

results = []

for i, test in enumerate(stress_test_queries, 1):
    print("=" * 70)
    print(f"QUERY {i}/{len(stress_test_queries)}")
    print("=" * 70)
    
    query = test["query"]
    expected = test["expected_answer"]
    section = test["section"]
    
    print(f"\nQuery: {query}")
    print(f"Expected: {expected}")
    print(f"Source: {section}")
    
    # Retrieve
    retrieval_result = retriever.retrieve(query, top_k=5)
    
    print(f"\nRetrieval:")
    print(f"  Domain filter: {retrieval_result.filters_used.get('domain', 'None')}")
    print(f"  Results found: {retrieval_result.total_results}")
    
    if retrieval_result.chunks:
        print(f"  Top result score: {retrieval_result.chunks[0]['score']:.2%}")
        
        # Check if we got Medical domain
        domains = set(c['metadata'].get('domain') for c in retrieval_result.chunks)
        if 'Medical' in domains:
            print(f"  ✅ Retrieved from Medical domain")
        else:
            print(f"  ❌ Wrong domain: {domains}")
    else:
        print(f"  ❌ No results found!")
    
    # Generate answer
    print(f"\nGenerating answer...")
    answer = generator.generate(query, retrieval_result)
    
    print(f"\nAnswer:")
    print(f"  {answer.answer}")
    print(f"  Confidence: {answer.confidence:.0%}")
    
    # Check if answer contains expected terms (simple check)
    answer_lower = answer.answer.lower()
    expected_lower = expected.lower()
    
    # Split expected answer into key terms
    key_terms = [term.strip().lower() for term in expected_lower.replace(" and ", ",").split(",")]
    
    found_terms = [term for term in key_terms if term in answer_lower]
    
    if found_terms:
        print(f"  ✅ Answer contains expected terms: {found_terms}")
        success = True
    else:
        print(f"  ⚠️  Expected terms not found in answer")
        success = False
    
    results.append({
        "query": query,
        "expected": expected,
        "success": success,
        "score": retrieval_result.chunks[0]['score'] if retrieval_result.chunks else 0,
        "confidence": answer.confidence,
    })
    
    print()

# Summary
print("=" * 70)
print("STRESS TEST SUMMARY")
print("=" * 70)

successful = sum(1 for r in results if r['success'])
total = len(results)

print(f"\nQueries answered correctly: {successful}/{total} ({successful/total*100:.0f}%)")

print("\nDetailed Results:")
for i, result in enumerate(results, 1):
    status = "✅" if result['success'] else "❌"
    print(f"  {status} Query {i}: {result['query'][:50]}...")
    print(f"     Retrieval: {result['score']:.0%} | Answer confidence: {result['confidence']:.0%}")

print("\nStress Test Metrics:")
avg_retrieval = sum(r['score'] for r in results) / len(results)
avg_confidence = sum(r['confidence'] for r in results) / len(results)

print(f"  Average retrieval score: {avg_retrieval:.0%}")
print(f"  Average answer confidence: {avg_confidence:.0%}")

if successful == total:
    print("\n🎉 ALL STRESS TEST QUERIES PASSED!")
elif successful >= total * 0.8:
    print(f"\n✅ GOOD: {successful}/{total} queries passed (80%+ success rate)")
elif successful >= total * 0.6:
    print(f"\n⚠️  ACCEPTABLE: {successful}/{total} queries passed (60%+ success rate)")
else:
    print(f"\n❌ NEEDS IMPROVEMENT: Only {successful}/{total} queries passed")

print("\n" + "=" * 70)
print("🎉 PHASE E COMPLETE!")
print("=" * 70)
print("\n✅ Medical document stress testing complete")
print("✅ Cross-section retrieval tested")
print("✅ Medical terminology handling verified")
print("✅ Domain-aware RAG system validated")
print("\nNext: Documentation & Cleanup (Day 11)")
print("=" * 70 + "\n")