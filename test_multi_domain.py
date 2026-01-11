# test_multi_domain.py
from src.retrieval.retriever import get_retriever

retriever = get_retriever()

queries = [
    ("Which hormone affects blood glucose?", "Medical"),
    ("How do I request annual leave?", "HR"),
    ("How do I deploy to kubernetes?", "Engineering"),
    ("What's the Q3 budget?", "Finance"),
]

for query, expected_domain in queries:
    result = retriever.retrieve(query, top_k=3)
    
    actual_domain = result.filters_used.get('domain', ['None'])[0] if result.filters_used else 'None'
    
    status = "✅" if actual_domain == expected_domain else "❌"
    print(f"{status} '{query[:40]}...' → Domain: {actual_domain} (expected: {expected_domain})")
    print(f"   Results: {result.total_results}\n")