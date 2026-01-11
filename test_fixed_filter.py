# test_fixed_filter.py
from src.retrieval.retriever import get_retriever

retriever = get_retriever()

# This should now work with filters enabled
result = retriever.retrieve(
    "Which hormone affects blood glucose?",
    top_k=5,
    use_query_understanding=True  # Re-enable!
)

print(f"\nReformulated: {result.reformulated_query}")
print(f"Domain filter: {result.filters_used}")
print(f"Results found: {result.total_results}")

if result.chunks:
    for i, chunk in enumerate(result.chunks[:3], 1):
        print(f"\n{i}. Score: {chunk['score']:.2%}")
        print(f"   Domain: {chunk['metadata'].get('domain')}")
        print(f"   Text: {chunk['text'][:100]}...")