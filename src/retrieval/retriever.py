
"""
Document retrieval with metadata filtering.
Combines vector similarity search with structured metadata filters.
"""

import json
from typing import Any

from config.settings import settings
from src.metadata.prompt_loader import get_prompt_loader
from src.storage.qdrant_manager import get_qdrant_manager
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

logger = get_logger(__name__)


class QueryResult:
    """
    Result from a retrieval query.
    
    Attributes:
        query: Original query
        reformulated_query: LLM-optimized query
        intent: Query intent type
        chunks: Retrieved chunks with metadata
        filters_used: Metadata filters applied
        total_results: Number of results found
    """
    
    def __init__(
        self,
        query: str,
        reformulated_query: str,
        intent: str,
        chunks: list[dict[str, Any]],
        filters_used: dict[str, Any],
    ) -> None:
        self.query = query
        self.reformulated_query = reformulated_query
        self.intent = intent
        self.chunks = chunks
        self.filters_used = filters_used
        self.total_results = len(chunks)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "reformulated_query": self.reformulated_query,
            "intent": self.intent,
            "total_results": self.total_results,
            "filters_used": self.filters_used,
            "chunks": self.chunks,
        }


class Retriever:
    """
    Retrieves relevant document chunks using metadata-filtered vector search.
    
    Features:
    - Query understanding with LLM
    - Metadata filter extraction
    - Vector similarity search
    - Results ranking
    """
    
    def __init__(self) -> None:
        self.qdrant = get_qdrant_manager()
        self.llm_client = get_llm_client()
        self.prompt_loader = get_prompt_loader()
        
        logger.info("retriever_initialized")

    def _detect_domain_fallback(self, query: str) -> str | None:
        """
        Fallback domain detection using keyword matching.
        
        Args:
            query: User query
            
        Returns:
            Domain name or None
        """
        query_lower = query.lower()
        
        # Medical keywords
        medical_keywords = [
            'disease', 'symptom', 'diagnosis', 'treatment', 'hormone', 
            'glucose', 'blood', 'patient', 'clinical', 'medical', 'infection',
            'pathology', 'anatomy', 'cardiovascular', 'dopaminergic', 'imaging',
            'pharmacology', 'adme', 'inflammation', 'parkinson', 'insulin'
        ]
        
        # HR keywords
        hr_keywords = [
            'employee', 'leave', 'vacation', 'pto', 'benefits', 'sick leave',
            'remote work', 'policy', 'onboarding', 'manager', 'annual leave'
        ]
        
        # Engineering keywords
        eng_keywords = [
            'deploy', 'kubernetes', 'api', 'code', 'docker', 'infrastructure',
            'technical', 'software', 'ci/cd', 'deployment'
        ]
        
        # Count matches
        medical_score = sum(1 for kw in medical_keywords if kw in query_lower)
        hr_score = sum(1 for kw in hr_keywords if kw in query_lower)
        eng_score = sum(1 for kw in eng_keywords if kw in query_lower)
        
        # Return domain with highest score
        scores = {
            'Medical': medical_score,
            'HR': hr_score,
            'Engineering': eng_score,
        }
        
        max_domain = max(scores.items(), key=lambda x: x[1])
        
        if max_domain[1] > 0:  # At least one keyword matched
            logger.info("fallback_domain_detection", domain=max_domain[0], score=max_domain[1])
            return max_domain[0]
        
        return None
    
    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        use_query_understanding: bool = True,
    ) -> QueryResult:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            top_k: Number of results to return (default: from settings)
            use_query_understanding: Whether to use LLM for query analysis
            
        Returns:
            QueryResult with retrieved chunks
        """
        top_k = top_k or settings.top_k_retrieval
        
        logger.info(
            "retrieval_started",
            query=query,
            top_k=top_k,
            use_understanding=use_query_understanding,
        )
        
        if use_query_understanding:
            # Understand query
            query_analysis = self._understand_query(query)
            
            reformulated_query = query_analysis.get("reformulated_query", query)
            intent = query_analysis.get("intent", "factual")
            filters = self._build_filters(query_analysis)
            
            # 🆕 NEW: Enhance medical queries with dictionary
            detected_domain = query_analysis.get("required_filters", {}).get("domain", [])
            if detected_domain and detected_domain[0] == "Medical":
                try:
                    from src.retrieval.query_enhancer import get_query_enhancer
                    
                    enhancer = get_query_enhancer()
                    enhancement = enhancer.enhance_medical_query(query, "Medical")
                    
                    # Use enhanced query if available
                    if enhancement["enhanced"]:
                        reformulated_query = enhancement["enhanced_query"]
                        logger.info(
                            "using_enhanced_query",
                            terms_defined=len(enhancement["definitions"])
                        )
                except Exception as e:
                    logger.warning("query_enhancement_failed", error=str(e))

            reformulated_query = query_analysis.get(
                "reformulated_query", query
            )
            intent = query_analysis.get("intent", "factual")
            filters = self._build_filters(query_analysis)
        else:
            # Direct search without query understanding
            reformulated_query = query
            intent = "factual"
            filters = None
        
        # Search Qdrant
        results = self.qdrant.search(
            query=reformulated_query,
            n_results=top_k,
            where=filters,
        )
        
        # Format results
        chunks = self._format_results(results)
        
        logger.info(
            "retrieval_completed",
            original_query=query,
            reformulated=reformulated_query,
            intent=intent,
            results_found=len(chunks),
            filters_used=filters is not None,
        )
        
        return QueryResult(
            query=query,
            reformulated_query=reformulated_query,
            intent=intent,
            chunks=chunks,
            filters_used=filters or {},
        )
    
    def retrieve_cross_domain(
        self,
        query: str,
        top_k: int | None = None,
        use_query_understanding: bool = True,
    ) -> QueryResult:
        """
        Retrieve relevant chunks WITHOUT domain filtering.
        
        Use this for queries that might span multiple domains.
        
        Args:
            query: User query
            top_k: Number of results to return
            use_query_understanding: Whether to use LLM for query analysis
            
        Returns:
            QueryResult with retrieved chunks (no domain filter applied)
        """
        top_k = top_k or settings.top_k_retrieval
        
        logger.info(
            "cross_domain_retrieval_started",
            query=query,
            top_k=top_k,
        )
        
        if use_query_understanding:
            # Get query analysis
            query_analysis = self._understand_query(query)
            
            # Remove domain from required filters to allow cross-domain search
            if "required_filters" in query_analysis and "domain" in query_analysis["required_filters"]:
                query_analysis["required_filters"].pop("domain", None)
                logger.info("domain_filter_removed_for_cross_domain_search")
            
            reformulated_query = query_analysis.get("reformulated_query", query)
            intent = query_analysis.get("intent", "factual")
            filters = self._build_filters(query_analysis)
        else:
            reformulated_query = query
            intent = "factual"
            filters = None
        
        # Search without domain constraint
        results = self.qdrant.search(
            query=reformulated_query,
            n_results=top_k,
            where=filters,  # ← This is wrong
        )

        # NEW:
        results = self.qdrant.search(
            query=reformulated_query,
            n_results=top_k,
            where=filters,  # Now filters is a Filter object
        )
        
        # Format results
        chunks = self._format_results(results)
        
        logger.info(
            "cross_domain_retrieval_completed",
            original_query=query,
            reformulated=reformulated_query,
            results_found=len(chunks),
        )
        
        return QueryResult(
            query=query,
            reformulated_query=reformulated_query,
            intent=intent,
            chunks=chunks,
            filters_used=filters or {},
        )
    
    def _understand_query(self, query: str) -> dict[str, Any]:
        """
        Use LLM to understand query intent and extract filters.
        
        Args:
            query: User query
            
        Returns:
            Query analysis dictionary
        """
        logger.debug("understanding_query", query=query)
        
        # Load and format prompt
        prompt = self.prompt_loader.get_prompt_text(
            "query_understanding",
            query=query,
        )

         # 🆕 ADD THIS DEBUG LOG
        logger.info("PROMPT_DEBUG", prompt_preview=prompt[:500], query=query)
        print(f"\n🔍 PROMPT PREVIEW (first 500 chars):\n{prompt[:500]}\n")
        print(f"🔍 ACTUAL QUERY BEING SENT: {query}\n")
    
        
        # Get analysis from LLM
        try:
            analysis = self.llm_client.complete_json(
                prompt=prompt,
                temperature=0.2,  # Some creativity for reformulation
                max_tokens=300,
            )
            
            # 🆕 FALLBACK: If LLM detected wrong domain, use keyword matching
            llm_domain = analysis.get("required_filters", {}).get("domain", [])
            fallback_domain = self._detect_domain_fallback(query)
            
            if fallback_domain and (not llm_domain or llm_domain[0] != fallback_domain):
                logger.warning(
                    "domain_mismatch_using_fallback",
                    llm_domain=llm_domain,
                    fallback_domain=fallback_domain,
                    query=query
                )
                # Override with fallback
                if "required_filters" not in analysis:
                    analysis["required_filters"] = {}
                analysis["required_filters"]["domain"] = [fallback_domain]

            logger.debug(
                "query_understood",
                intent=analysis.get("intent"),
                confidence=analysis.get("confidence"),
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error("query_understanding_json_failed", error=str(e))
            # Fallback to original query
            return {
                "intent": "factual",
                "query_type": "simple_lookup",
                "required_filters": {},
                "optional_filters": {},
                "reformulated_query": query,
                "confidence": 0.5,
            }
        except Exception as e:
            logger.error("query_understanding_failed", error=str(e))
            # Fallback to original query
            return {
                "intent": "factual",
                "query_type": "simple_lookup",
                "required_filters": {},
                "optional_filters": {},
                "reformulated_query": query,
                "confidence": 0.5,
            }
    
    def _build_filters(self, query_analysis: dict[str, Any]) -> Filter | None:
        """
        Build Qdrant filter from query analysis.
        
        Args:
            query_analysis: Analysis from query understanding
            
        Returns:
            Qdrant Filter object or None
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
        
        required_filters = query_analysis.get("required_filters", {})
        
        if not required_filters:
            return None
        
        conditions = []
        
        # PRIORITY 1: Domain filter (MOST IMPORTANT)
        if "domain" in required_filters and required_filters["domain"]:
            domains = required_filters["domain"]
            
            logger.info("building_domain_filter", domains=domains)
            
            if len(domains) == 1:
                # Single domain
                conditions.append(
                    FieldCondition(
                        key="domain",
                        match=MatchValue(value=domains[0])
                    )
                )
            else:
                # Multiple domains - use MatchAny
                conditions.append(
                    FieldCondition(
                        key="domain",
                        match=MatchAny(any=domains)
                    )
                )
        
        # PRIORITY 2: Document type (if specified)
        if "document_type" in required_filters and required_filters["document_type"]:
            doc_types = required_filters["document_type"]
            
            if len(doc_types) == 1:
                conditions.append(
                    FieldCondition(
                        key="document_type",
                        match=MatchValue(value=doc_types[0])
                    )
                )
            else:
                conditions.append(
                    FieldCondition(
                        key="document_type",
                        match=MatchAny(any=doc_types)
                    )
                )
        
        # PRIORITY 3: Department (if specified)
        if "department" in required_filters and required_filters["department"]:
            depts = required_filters["department"]
            
            if len(depts) == 1:
                conditions.append(
                    FieldCondition(
                        key="department",
                        match=MatchValue(value=depts[0])
                    )
                )
            else:
                conditions.append(
                    FieldCondition(
                        key="department",
                        match=MatchAny(any=depts)
                    )
                )
        
        # Return Filter object (not dict!)
        if conditions:
            return Filter(must=conditions)
        else:
            return None
        
    def _format_results(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Format Qdrant results into structured chunks.
        
        Args:
            results: Raw results from Qdrant
            
        Returns:
            List of formatted chunk dictionaries
        """
        chunks = []
        
        if not results["ids"]:
            return chunks
        
        distances = results["distances"]
        
        # Normalize distances to 0-1 similarity scores
        # Lower distance = higher similarity
        if distances:
            min_dist = min(distances)
            max_dist = max(distances)
            dist_range = max_dist - min_dist if max_dist > min_dist else 1.0
        else:
            min_dist = 0
            dist_range = 1.0
        
        for i in range(len(results["ids"])):
            distance = distances[i]
            
            # Normalize: closest = 1.0, farthest = 0.0
            if dist_range > 0:
                score = 1.0 - ((distance - min_dist) / dist_range)
            else:
                score = 1.0
            
            # Ensure score is in [0, 1]
            score = max(0.0, min(1.0, score))
            
            chunk = {
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "distance": distance,
                "score": score,
            }
            chunks.append(chunk)
        
        return chunks
    


# Global retriever instance
_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    """
    Get or create the global retriever instance.
    
    Returns:
        Singleton Retriever instance
    """
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
