# quick_check.py
from src.storage.qdrant_manager import get_qdrant_manager
from qdrant_client.models import Filter, FieldCondition, MatchValue

qdrant = get_qdrant_manager()

# Check what's actually stored
result = qdrant.client.scroll(
    collection_name="company_docs",
    limit=10
)

print("First 3 chunks in database:")
for point in result[0][:3]:
    print(f"\nID: {point.id}")
    print(f"Domain field: {point.payload.get('domain', 'MISSING!')}")
    print(f"All payload keys: {list(point.payload.keys())}")
    print(f"Text preview: {point.payload.get('text', '')[:100]}")