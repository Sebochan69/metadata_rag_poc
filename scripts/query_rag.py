"""
CLI script to query the RAG system.

Usage:
    python scripts/query_rag.py "How do I request time off?"
    python scripts/query_rag.py "What's the remote work policy?" --top-k 5
    python scripts/query_rag.py "Leave policy" --no-answer  # Just retrieval
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generation.answer_generator import get_answer_generator
from src.retrieval.retriever import get_retriever
from src.storage.chroma_manager import get_chroma_manager


def display_answer(answer, show_sources: bool = True, show_metadata: bool = False):
    """
    Display the generated answer with formatting.
    
    Args:
        answer: Answer object
        show_sources: Whether to show source information
        show_metadata: Whether to show detailed metadata
    """
    print(f"\n{'=' * 60}")
    print(f"ANSWER")
    print(f"{'=' * 60}")
    print(f"\n{answer.answer}\n")
    
    if show_sources and answer.sources:
        print(f"{'─' * 60}")
        print(f"SOURCES ({len(answer.sources)} document(s))")
        print(f"{'─' * 60}")
        
        for i, source in enumerate(answer.sources, 1):
            print(f"\n{i}. {source['document_type']} | {source['department']}")
            print(f"   Authority: {source['authority_level']}")
            print(f"   Relevance: {source['score']:.2%}")
            
            if show_metadata:
                if 'effective_date' in source:
                    print(f"   Effective: {source['effective_date']}")
                if 'version' in source:
                    print(f"   Version: {source['version']}")
    
    print(f"\n{'─' * 60}")
    print(f"Confidence: {answer.confidence:.0%} | Context used: {answer.context_used} chunk(s)")
    print(f"{'=' * 60}\n")


def display_retrieval_results(retrieval_result, show_text: bool = False):
    """
    Display retrieval results without answer generation.
    
    Args:
        retrieval_result: QueryResult object
        show_text: Whether to show chunk text
    """
    print(f"\n{'=' * 60}")
    print(f"RETRIEVAL RESULTS")
    print(f"{'=' * 60}")
    print(f"\nQuery: {retrieval_result.query}")
    print(f"Reformulated: {retrieval_result.reformulated_query}")
    print(f"Intent: {retrieval_result.intent}")
    print(f"Results found: {retrieval_result.total_results}")
    
    if retrieval_result.filters_used:
        print(f"\nFilters applied:")
        for key, value in retrieval_result.filters_used.items():
            print(f"  - {key}: {value}")
    
    if retrieval_result.chunks:
        print(f"\n{'─' * 60}")
        print(f"TOP RESULTS")
        print(f"{'─' * 60}")
        
        for i, chunk in enumerate(retrieval_result.chunks, 1):
            meta = chunk['metadata']
            print(f"\n{i}. Score: {chunk['score']:.2%}")
            print(f"   Type: {meta.get('document_type', 'Unknown')}")
            print(f"   Dept: {meta.get('department', 'Unknown')}")
            print(f"   Authority: {meta.get('authority_level', 'Unknown')}")
            
            if show_text:
                text_preview = chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
                print(f"   Text: {text_preview}")
    
    print(f"\n{'=' * 60}\n")


def interactive_mode():
    """
    Run interactive query mode.
    """
    print(f"\n{'=' * 60}")
    print("RAG SYSTEM - Interactive Mode")
    print(f"{'=' * 60}")
    print("Type your questions. Commands:")
    print("  - 'stats' : Show collection statistics")
    print("  - 'exit' or 'quit' : Exit")
    print(f"{'=' * 60}\n")
    
    retriever = get_retriever()
    generator = get_answer_generator()
    chroma = get_chroma_manager()
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye! 👋\n")
                break
            
            if query.lower() == 'stats':
                stats = chroma.get_collection_stats()
                print(f"\n📊 Collection Statistics:")
                print(f"   Name: {stats['collection_name']}")
                print(f"   Total chunks: {stats['total_chunks']}")
                print(f"   Directory: {stats['persist_directory']}")
                continue
            
            # Process query
            print("\n⏳ Processing...")
            
            # Retrieve
            retrieval_result = retriever.retrieve(query)
            
            if not retrieval_result.chunks:
                print("\n❌ No relevant documents found.")
                print("   Try rephrasing your question or check if documents are ingested.")
                continue
            
            # Generate answer
            answer = generator.generate(query, retrieval_result)
            
            # Display
            display_answer(answer, show_sources=True, show_metadata=False)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Query the RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single query with answer
  python scripts/query_rag.py "How do I request time off?"
  
  # Query with more results
  python scripts/query_rag.py "What's the remote work policy?" --top-k 5
  
  # Just retrieval, no answer
  python scripts/query_rag.py "Leave policy" --no-answer
  
  # Show chunk text
  python scripts/query_rag.py "Benefits" --no-answer --show-text
  
  # Interactive mode
  python scripts/query_rag.py --interactive
  
  # Show collection stats
  python scripts/query_rag.py --stats
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        type=str,
        help='Question to ask (required unless using --interactive or --stats)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of chunks to retrieve (default: 5)'
    )
    parser.add_argument(
        '--no-answer',
        action='store_true',
        help='Only show retrieval results, no answer generation'
    )
    parser.add_argument(
        '--show-text',
        action='store_true',
        help='Show chunk text in retrieval results'
    )
    parser.add_argument(
        '--show-metadata',
        action='store_true',
        help='Show detailed source metadata'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show collection statistics'
    )
    
    args = parser.parse_args()
    
    # Handle special modes
    if args.stats:
        chroma = get_chroma_manager()
        stats = chroma.get_collection_stats()
        print(f"\n{'=' * 60}")
        print("COLLECTION STATISTICS")
        print(f"{'=' * 60}")
        print(f"Collection: {stats['collection_name']}")
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Location: {stats['persist_directory']}")
        print(f"{'=' * 60}\n")
        return
    
    if args.interactive:
        interactive_mode()
        return
    
    # Require query for non-interactive mode
    if not args.query:
        parser.error("Query required (or use --interactive or --stats)")
    
    # Process single query
    print(f"\n⏳ Processing query...\n")
    
    try:
        # Retrieve
        retriever = get_retriever()
        retrieval_result = retriever.retrieve(args.query, top_k=args.top_k)
        
        if not retrieval_result.chunks:
            print("❌ No relevant documents found.")
            print("   Try rephrasing your question or check if documents are ingested.\n")
            sys.exit(1)
        
        if args.no_answer:
            # Just show retrieval results
            display_retrieval_results(retrieval_result, show_text=args.show_text)
        else:
            # Generate and show answer
            generator = get_answer_generator()
            answer = generator.generate(args.query, retrieval_result)
            display_answer(answer, show_sources=True, show_metadata=args.show_metadata)
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()