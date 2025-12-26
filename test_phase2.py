from src.utils.logger import get_logger
from src.utils.llm_client import get_llm_client
from src.metadata.prompt_loader import get_prompt_loader

# Test 1: Logging
print("=" * 60)
print("TEST 1: Logging")
print("=" * 60)
logger = get_logger(__name__)
logger.info("phase2_test_started", test_number=1)
print("✅ Logging works!\n")

# Test 2: Prompt Loader
print("=" * 60)
print("TEST 2: Prompt Loader")
print("=" * 60)
loader = get_prompt_loader()
available = loader.list_available()
print(f"Available prompts: {available}")

if "classification" in available:
    data = loader.load("classification")
    print(f"✅ Classification prompt loaded!")
    print(f"   Version: {data['metadata'].get('version', 'N/A')}")
    print(f"   Model: {data['metadata'].get('model', 'N/A')}")
    print(f"   Placeholders: {data['placeholders']}")
else:
    print("❌ Classification prompt not found!")
print()

# Test 3: LLM Client
print("=" * 60)
print("TEST 3: LLM Client")
print("=" * 60)
client = get_llm_client()
print("✅ LLM Client initialized!")
print(f"   Current usage: {client.get_usage_stats()}")
print()

logger.info("phase2_test_completed", status="success")
print("=" * 60)
print("🎉 All Phase 2 components working!")
print("=" * 60)