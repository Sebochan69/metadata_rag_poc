CLASSIFICATION_PROMPT = """
Analyze this document and classify it.

Document Preview:
{document_preview}

Return ONLY valid JSON:
{{
  "complexity": "simple|structured|complex",
  "document_type": "HR Policy|Technical Manual|...",
  "requires_deep_analysis": true|false,
  "confidence": 0.0-1.0
}}
"""

DOC_METADATA_PROMPT = """
Extract metadata from this document.

Full Document:
{full_text}

Return ONLY valid JSON matching this schema:
{{
  "document_type": "...",
  "department": "...",
  "topics": ["..."],
  "authority_level": "official|draft|archived",
  "effective_date": "YYYY-MM-DD",
  "intended_audience": ["..."],
  "document_summary": "2-3 sentence summary"
}}
"""

# More prompts...