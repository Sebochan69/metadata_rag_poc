"""
Test Merriam-Webster enhancement.
"""
from src.retrieval.query_enhancer import get_query_enhancer

enhancer = get_query_enhancer()

if not enhancer.enabled:
    print("❌ Enhancement disabled - add API keys to .env")
    print("   MERRIAM_WEBSTER_MEDICAL_KEY=...")
    print("   MERRIAM_WEBSTER_DICT_KEY=...")
else:
    print("✅ Enhancement enabled\n")
    
    # Test medical query
    result = enhancer.enhance_medical_query(
        "Which hormone affects blood glucose?",
        domain="Medical"
    )
    
    print(f"Original: {result['original_query']}")
    print(f"Enhanced: {result['enhanced']}")
    print(f"\nDefinitions found: {len(result['definitions'])}")
    
    for d in result['definitions']:
        print(f"  • {d['term']}: {d['definition']}")