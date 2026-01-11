# reset_db.py
from src.storage.qdrant_manager import get_qdrant_manager

qdrant = get_qdrant_manager()
qdrant.reset_collection()

print("✅ Database reset - ready for re-ingestion")