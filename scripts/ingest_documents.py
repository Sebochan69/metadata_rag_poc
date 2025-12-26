"""
CLI script to ingest documents into the RAG system.

Usage:
    python scripts/ingest_documents.py --file path/to/document.pdf
    python scripts/ingest_documents.py --directory path/to/docs --pattern "*.pdf"
    python scripts/ingest_documents.py --file doc.pdf --doc-id custom_id_001
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.pdf_loader import load_document
from src.orchestration.graph import run_extraction
from src.storage.chroma_manager import get_chroma_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def ingest_single_file(
    file_path: str,
    document_id: str | None = None,
) -> bool:
    """
    Ingest a single document.
    
    Args:
        file_path: Path to document
        document_id: Optional custom document ID
        
    Returns:
        True if successful, False otherwise
    """
    file_path_obj = Path(file_path)
    
    # Generate doc ID from filename if not provided
    if document_id is None:
        document_id = file_path_obj.stem
    
    print(f"\n{'=' * 60}")
    print(f"Processing: {file_path_obj.name}")
    print(f"Document ID: {document_id}")
    print(f"{'=' * 60}")
    
    try:
        # 1. Load document
        print("\n[1/3] Loading document...")
        text = load_document(file_path)
        print(f"✅ Loaded: {len(text)} characters, {len(text.split())} words")
        
        # 2. Extract metadata and chunk
        print("\n[2/3] Extracting metadata and chunking...")
        result = run_extraction(
            document_id=document_id,
            document_text=text,
            filename=file_path_obj.name,
        )
        
        if result['status'] != 'completed':
            print(f"❌ Extraction failed: {result.get('error')}")
            return False
        
        print(f"✅ Metadata extracted:")
        print(f"   Type: {result['doc_metadata']['document_type']}")
        print(f"   Department: {result['doc_metadata']['department']}")
        print(f"   Topics: {', '.join(result['doc_metadata']['topics'][:5])}")
        print(f"   Chunks: {len(result['chunks'])}")
        print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
        print(f"   Cost: ${result.get('estimated_cost', 0):.4f}")
        
        # 3. Store in vector database
        print("\n[3/3] Storing in vector database...")
        chroma = get_chroma_manager()
        chroma.add_chunks(result['chunks'], document_id)
        
        stats = chroma.get_collection_stats()
        print(f"✅ Stored successfully")
        print(f"   Total chunks in DB: {stats['total_chunks']}")
        
        print(f"\n{'=' * 60}")
        print(f"🎉 {file_path_obj.name} ingested successfully!")
        print(f"{'=' * 60}\n")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        logger.error("ingest_file_failed", file=file_path, error=str(e))
        return False


def ingest_directory(
    directory: str,
    pattern: str = "*.pdf",
    recursive: bool = False,
) -> dict[str, int]:
    """
    Ingest all documents in a directory.
    
    Args:
        directory: Directory path
        pattern: File pattern (default: *.pdf)
        recursive: Search recursively
        
    Returns:
        Dictionary with success/failure counts
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ Directory not found: {directory}")
        return {"success": 0, "failed": 0}
    
    # Find files
    if recursive:
        files = list(dir_path.rglob(pattern))
    else:
        files = list(dir_path.glob(pattern))
    
    if not files:
        print(f"❌ No files matching '{pattern}' found in {directory}")
        return {"success": 0, "failed": 0}
    
    print(f"\n{'=' * 60}")
    print(f"Found {len(files)} file(s) to process")
    print(f"{'=' * 60}")
    
    success_count = 0
    failed_count = 0
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}]", end=" ")
        
        if ingest_single_file(str(file_path)):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"Batch Ingestion Complete")
    print(f"{'=' * 60}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"Total: {len(files)}")
    print(f"{'=' * 60}\n")
    
    return {"success": success_count, "failed": failed_count}


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ingest documents into the RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a single PDF
  python scripts/ingest_documents.py --file data/raw/policy.pdf
  
  # Ingest with custom ID
  python scripts/ingest_documents.py --file policy.pdf --doc-id hr_policy_001
  
  # Ingest all PDFs in a directory
  python scripts/ingest_documents.py --directory data/raw
  
  # Ingest all markdown files recursively
  python scripts/ingest_documents.py --directory docs --pattern "*.md" --recursive
        """
    )
    
    # Mutually exclusive: file or directory
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--file',
        type=str,
        help='Path to a single document file'
    )
    group.add_argument(
        '--directory',
        type=str,
        help='Path to directory containing documents'
    )
    
    # Optional arguments
    parser.add_argument(
        '--doc-id',
        type=str,
        help='Custom document ID (only for --file)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.pdf',
        help='File pattern for directory mode (default: *.pdf)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Search directory recursively'
    )
    
    args = parser.parse_args()
    
    # Process based on mode
    if args.file:
        success = ingest_single_file(args.file, args.doc_id)
        sys.exit(0 if success else 1)
    else:
        results = ingest_directory(
            args.directory,
            args.pattern,
            args.recursive
        )
        sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()