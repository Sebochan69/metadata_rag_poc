from src.metadata.classifier import get_classifier
from src.metadata.validator import get_validator
from config.business_rules import validate_metadata_completeness

print("=" * 60)
print("TEST: Phase 3 - Classification & Validation")
print("=" * 60)

# Test 1: Classifier
classifier = get_classifier()
print("✅ Classifier initialized")

# Test 2: Validator
validator = get_validator()
print("✅ Validator initialized")

# Test 3: Business rules
test_metadata = {
    "document_type": "HR Policy",
    "department": "HR",
    "authority_level": "official",
    "topics": ["annual_leave"],
    "intended_audience": ["all_employees"],
}
errors = validate_metadata_completeness(test_metadata)
print(f"✅ Business rules validation: {len(errors)} errors")

print("\n" + "=" * 60)
print("🎉 Phase 3 complete!")
print("=" * 60)