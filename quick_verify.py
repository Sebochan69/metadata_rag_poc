# quick_verify.py
from src.storage.qdrant_manager import get_qdrant_manager

qdrant = get_qdrant_manager()

# Get all chunks
result = qdrant.client.scroll(
    collection_name="company_docs",
    limit=20
)

# Count by domain
from collections import Counter
domains = [p.payload.get('domain') for p in result[0]]
print(Counter(domains))
