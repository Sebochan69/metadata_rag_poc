"""
Loads prompts from markdown files for LLM calls.
Provides caching and validation of prompt templates.
"""

import re
from pathlib import Path
from typing import Any

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PromptLoader:
    """
    Load and manage markdown-based prompts.
    
    Features:
    - Loads prompts from markdown files
    - Caches loaded prompts for performance
    - Extracts metadata (version, model, temperature)
    - Supports string formatting with variables
    """
    
    def __init__(self, prompts_dir: Path | None = None) -> None:
        """
        Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing markdown prompts
                        (defaults to settings.prompts_dir)
        """
        self.prompts_dir = prompts_dir or settings.prompts_dir
        self._cache: dict[str, dict[str, Any]] = {}
        
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Prompts directory not found: {self.prompts_dir}"
            )
        
        logger.info("prompt_loader_initialized", prompts_dir=str(self.prompts_dir))
    
    def load(self, prompt_name: str) -> dict[str, Any]:
        """
        Load a prompt from markdown file.
        
        Args:
            prompt_name: Name of the prompt file (without .md extension)
            
        Returns:
            Dictionary containing:
                - prompt: The actual prompt text
                - metadata: Extracted metadata (version, model, etc.)
                
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            
        Example:
            >>> loader = PromptLoader()
            >>> data = loader.load("classification")
            >>> prompt_text = data["prompt"]
            >>> version = data["metadata"]["version"]
        """
        # Check cache
        if prompt_name in self._cache:
            logger.debug("prompt_loaded_from_cache", prompt_name=prompt_name)
            return self._cache[prompt_name]
        
        # Load from file
        file_path = self.prompts_dir / f"{prompt_name}.md"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {file_path}\n"
                f"Available prompts: {self.list_available()}"
            )
        
        logger.info("loading_prompt", prompt_name=prompt_name, path=str(file_path))
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse markdown
        metadata = self._extract_metadata(content)
        prompt = self._extract_prompt_section(content)
        
        # Validate prompt has required placeholders if any
        placeholders = self._extract_placeholders(prompt)
        
        result = {
            "prompt": prompt,
            "metadata": metadata,
            "placeholders": placeholders,
        }
        
        # Cache result
        self._cache[prompt_name] = result
        
        logger.info(
            "prompt_loaded",
            prompt_name=prompt_name,
            version=metadata.get("version", "unknown"),
            placeholders=placeholders,
        )
        
        return result
    
    def get_prompt_text(self, prompt_name: str, **kwargs: Any) -> str:
        """
        Get formatted prompt text with variables substituted.
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            Formatted prompt text
            
        Example:
            >>> loader = PromptLoader()
            >>> prompt = loader.get_prompt_text(
            ...     "classification",
            ...     document_preview="This is a memo..."
            ... )
        """
        data = self.load(prompt_name)
        prompt_template = data["prompt"]
        
        # Check if all required placeholders are provided
        required = data["placeholders"]
        missing = set(required) - set(kwargs.keys())
        
        if missing:
            logger.warning(
                "missing_prompt_variables",
                prompt_name=prompt_name,
                missing=list(missing),
            )
        
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            logger.error(
                "prompt_formatting_failed",
                prompt_name=prompt_name,
                error=str(e),
                required_placeholders=required,
                provided_keys=list(kwargs.keys()),
            )
            raise
    
    def get_metadata(self, prompt_name: str) -> dict[str, Any]:
        """
        Get metadata for a prompt without loading the full prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Metadata dictionary
        """
        data = self.load(prompt_name)
        return data["metadata"]
    
    def list_available(self) -> list[str]:
        """
        List all available prompt names.
        
        Returns:
            List of prompt names (without .md extension)
        """
        prompt_files = self.prompts_dir.glob("*.md")
        return [f.stem for f in prompt_files if f.stem != "README"]
    
    def _extract_metadata(self, content: str) -> dict[str, Any]:
        """
        Extract metadata from markdown header.
        
        Looks for lines like:
        - **Version**: 1.0.0
        - **Model**: gpt-4o
        """
        metadata: dict[str, Any] = {}
        
        # Extract metadata section (between ## Metadata and next ##)
        metadata_pattern = r"## Metadata\s*\n(.*?)\n##"
        match = re.search(metadata_pattern, content, re.DOTALL)
        
        if match:
            metadata_text = match.group(1)
            
            # Parse key-value pairs
            for line in metadata_text.split("\n"):
                # Match patterns like: - **Key**: value
                kv_match = re.match(r"-\s*\*\*(.+?)\*\*:\s*(.+)", line.strip())
                if kv_match:
                    key = kv_match.group(1).lower().replace(" ", "_")
                    value = kv_match.group(2).strip()
                    metadata[key] = value
        
        return metadata
    
    def _extract_prompt_section(self, content: str) -> str:
        """
        Extract the ## Prompt: section from markdown.
        """
        # Find content between ## Prompt: and the next ##
        prompt_pattern = r"## Prompt:\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(prompt_pattern, content, re.DOTALL)
        
        if not match:
            raise ValueError("No '## Prompt:' section found in markdown")
        
        prompt = match.group(1).strip()
        return prompt
    
    def _extract_placeholders(self, prompt: str) -> list[str]:
        """
        Extract placeholder variables from prompt template.
        
        Finds all {variable_name} patterns.
        """
        placeholders = re.findall(r"\{(\w+)\}", prompt)
        return list(set(placeholders))  # Remove duplicates
    
    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()
        logger.info("prompt_cache_cleared")
    
    def reload(self, prompt_name: str) -> dict[str, Any]:
        """
        Reload a prompt from disk, bypassing cache.
        
        Args:
            prompt_name: Name of the prompt to reload
            
        Returns:
            Reloaded prompt data
        """
        if prompt_name in self._cache:
            del self._cache[prompt_name]
        return self.load(prompt_name)


# Global loader instance
_loader: PromptLoader | None = None


def get_prompt_loader() -> PromptLoader:
    """
    Get or create the global prompt loader instance.
    
    Returns:
        Singleton PromptLoader instance
    """
    global _loader
    if _loader is None:
        _loader = PromptLoader()
    return _loader