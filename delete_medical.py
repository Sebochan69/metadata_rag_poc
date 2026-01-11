# delete_medical.py
from src.storage.qdrant_manager import get_qdrant_manager

qdrant = get_qdrant_manager()
qdrant.delete_document("medical_compendium_stress_test")

print("✅ Medical document deleted")