"""
Query enhancement with Merriam-Webster dictionary lookup.
"""
import re
from typing import Any

import requests

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QueryEnhancer:
    """Enhances medical queries with dictionary definitions"""
    
    def __init__(self):
        self.medical_api_key = settings.merriam_webster_medical_key
        self.dict_api_key = settings.merriam_webster_dict_key
        self.base_url_medical = "https://www.dictionaryapi.com/api/v3/references/medical/json"
        self.base_url_dict = "https://www.dictionaryapi.com/api/v3/references/collegiate/json"
        
        # Check if keys are available
        self.enabled = bool(self.medical_api_key and self.dict_api_key)
        if self.enabled:
            logger.info("query_enhancer_initialized", enabled=True)
        else:
            logger.warning(
                "query_enhancer_disabled",
                reason="API keys not configured in .env"
            )
    
    def enhance_medical_query(self, query: str, domain: str) -> dict[str, Any]:
        """
        Enhance query with medical dictionary lookups.
        
        Args:
            query: Original query
            domain: Detected domain
            
        Returns:
            Enhanced query info with definitions
        """
        # If not medical domain or not enabled, return unchanged
        if domain != "Medical" or not self.enabled:
            return {
                "original_query": query,
                "enhanced_query": query,
                "definitions": [],
                "enhanced": False,
            }
        
        # Extract potential medical terms
        words = re.findall(r'\b[a-z]{4,}\b', query.lower())
        
        # Filter out common words
        stopwords = {
            'which', 'what', 'how', 'that', 'this', 'does', 'have',
            'with', 'from', 'they', 'been', 'were', 'their', 'about',
            'mentioned', 'affects', 'involves', 'uses', 'are'
        }
        medical_terms = [w for w in words if w not in stopwords]
        
        definitions = []
        
        # Look up first 3 medical terms
        for term in medical_terms[:3]:
            definition = self._lookup_medical_term(term)
            if definition:
                definitions.append({
                    "term": term,
                    "definition": definition
                })
        
        # Build enhanced query
        if definitions:
            # Add definitions as context
            context = "; ".join([
                f"{d['term']}: {d['definition']}"
                for d in definitions
            ])
            enhanced = f"{query}\n\nContext: {context}"
            
            logger.info(
                "query_enhanced",
                original=query,
                terms_defined=len(definitions)
            )
        else:
            enhanced = query
        
        return {
            "original_query": query,
            "enhanced_query": enhanced,
            "definitions": definitions,
            "enhanced": len(definitions) > 0,
        }
    
    def _lookup_medical_term(self, term: str) -> str | None:
        """
        Look up a term in Merriam-Webster Medical Dictionary.
        
        Args:
            term: Medical term to look up
            
        Returns:
            Definition string or None
        """
        try:
            url = f"{self.base_url_medical}/{term}?key={self.medical_api_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                logger.debug("dictionary_lookup_failed", term=term, status=response.status_code)
                return None
            
            data = response.json()
            
            # Check if we got a valid entry (not a suggestion list)
            if not data or not isinstance(data, list):
                return None
            
            first_entry = data[0]
            
            # If it's a string, it's a suggestion, not a definition
            if isinstance(first_entry, str):
                logger.debug("dictionary_suggestion_only", term=term, suggestion=first_entry)
                return None
            
            # Extract definition
            if isinstance(first_entry, dict) and 'shortdef' in first_entry:
                definitions = first_entry['shortdef']
                if definitions:
                    logger.info("dictionary_lookup_success", term=term)
                    return definitions[0]  # Return first definition
            
            return None
            
        except requests.Timeout:
            logger.warning("dictionary_timeout", term=term)
            return None
        except Exception as e:
            logger.warning("dictionary_error", term=term, error=str(e))
            return None


# Global instance
_enhancer: QueryEnhancer | None = None


def get_query_enhancer() -> QueryEnhancer:
    """
    Get or create the global query enhancer instance.
    
    Returns:
        Singleton QueryEnhancer instance
    """
    global _enhancer
    if _enhancer is None:
        _enhancer = QueryEnhancer()
    return _enhancer