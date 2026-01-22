"""
Batch ingest medical section files.

This ingests each section as a separate document,
creating more focused chunks for better retrieval precision.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.graph import run_extraction
from src.storage.qdrant_manager import get_qdrant_manager

print("=" * 70)
print("BATCH INGESTION: Medical Sections")
print("=" * 70)

# Get section files
sections_dir = Path("data/raw/medical_sections")

if not sections_dir.exists():
    print(f"\n❌ Sections directory not found: {sections_dir}")
    print("Run: python split_medical_sections.py first")
    sys.exit(1)

section_files = sorted(sections_dir.glob("*.txt"))

if not section_files:
    print(f"\n❌ No section files found in {sections_dir}")
    sys.exit(1)

print(f"\nFound {len(section_files)} section files to ingest")

# Reset Qdrant collection (clean start)
print(f"\n🗑️  Resetting Qdrant collection...")
qdrant = get_qdrant_manager()
qdrant.reset_collection()
print(f"✅ Collection reset")

# Ingest each section
results = {
    "success": 0,
    "failed": 0,
    "total_chunks": 0,
}

for i, section_file in enumerate(section_files, 1):
    print(f"\n{'=' * 70}")
    print(f"[{i}/{len(section_files)}] Processing: {section_file.name}")
    print(f"{'=' * 70}")
    
    # Read section
    with open(section_file, 'r', encoding='utf-8') as f:
        section_text = f.read()
    
    print(f"  Size: {len(section_text)} chars, {len(section_text.split())} words")
    
    # Extract metadata and chunk
    document_id = f"medical_section_{section_file.stem}"
    
    try:
        result = run_extraction(
            document_id=document_id,
            document_text=section_text,
            filename=section_file.name,
        )
        
        if result['status'] != 'completed':
            print(f"  ❌ Extraction failed: {result.get('error')}")
            results["failed"] += 1
            continue
        
        # Show results
        metadata = result['doc_metadata']
        chunks = result['chunks']
        
        print(f"  ✅ Extracted:")
        print(f"     Domain: {metadata.get('domain')}")
        print(f"     Topics: {metadata.get('topics', [])[:3]}...")
        print(f"     Chunks: {len(chunks)}")
        
        # Store in Qdrant
        qdrant.add_chunks(chunks, document_id)
        
        results["success"] += 1
        results["total_chunks"] += len(chunks)
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results["failed"] += 1

# Summary
print(f"\n{'=' * 70}")
print(f"BATCH INGESTION COMPLETE")
print(f"{'=' * 70}")
print(f"\n📊 Results:")
print(f"   ✅ Successful: {results['success']}/{len(section_files)}")
print(f"   ❌ Failed: {results['failed']}/{len(section_files)}")
print(f"   📦 Total chunks: {results['total_chunks']}")

# Get final stats
stats = qdrant.get_collection_stats()
print(f"\n💾 Qdrant Stats:")
print(f"   Total chunks in DB: {stats['total_chunks']}")

print(f"\n{'=' * 70}")
print(f"✅ READY FOR RETRIEVAL TESTING")
print(f"{'=' * 70}")
print(f"\nNext: python test_retrieval_quick.py")
print(f"{'=' * 70}\n")