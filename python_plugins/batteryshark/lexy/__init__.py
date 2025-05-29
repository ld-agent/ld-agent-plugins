# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Lexy Glossary Plugin",
    "description": "AI-powered glossary search and lookup tools with exact, fuzzy, and semantic search capabilities",
    "author": "BatteryShark",
    "version": "1.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": [
        "pydantic>=2.0.0", 
        "rapidfuzz>=3.0.0",
        "PyYAML>=6.0.0"
    ],
    "environment_variables": {
        "LEXY_GLOSSARY_PATH": {
            "description": "Path to the YAML glossary file",
            "default": "glossary.yaml",
            "required": False
        },
        "LEXY_LLM_MODEL": {
            "description": "AI model for semantic search (e.g., gemini-2.0-flash or gpt-4o)",
            "default": "gemini-2.0-flash",
            "required": False
        },       
        "LEXY_LLM_GEMINI_API_KEY": {
            "description": "LLM API key for Gemini models",
            "default": None,
            "required": False
        },       
        "LEXY_LLM_OPENAI_API_KEY": {
            "description": "LLM API key for OpenAI models",
            "default": None,
            "required": False
        }
    }
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

"""
Lexy Glossary Plugin - AI-powered glossary search and lookup tools.

This package provides intelligent search functionality for YAML-based glossaries
with exact, fuzzy, and semantic search capabilities.
"""

from typing import Annotated, List, Optional, Dict, Any
from pydantic import Field

# Import implementation functions
from .lexy_glossary_plugin import (
    lookup_term as _lookup_term_impl,
    batch_lookup_terms as _batch_lookup_terms_impl,
    fuzzy_search_terms as _fuzzy_search_terms_impl,
    smart_query as _smart_query_impl,
    list_terms as _list_terms_impl,
    initialize_plugin as _initialize_plugin_impl
)

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

async def lookup_term(
    term: Annotated[str, Field(description="The term to look up")]
) -> List[dict]:
    """
    Look up a specific term in the glossary with exact matching.
    
    Args:
        term: The term to look up
        
    Returns:
        List of matching terms (usually 1 for exact match, or suggestions if not found)
    """
    return await _lookup_term_impl(term)

async def batch_lookup_terms(
    terms: Annotated[List[str], Field(description="List of terms to look up")]
) -> dict:
    """
    Look up multiple terms at once to reduce round trips.
    
    Args:
        terms: List of terms to look up
        
    Returns:
        Dictionary mapping each term to its lookup results
    """
    return await _batch_lookup_terms_impl(terms)

async def fuzzy_search_terms(
    query: Annotated[str, Field(description="The search query")],
    threshold: Annotated[int, Field(description="Similarity threshold (0-100)")] = 80
) -> List[dict]:
    """
    Search for terms using fuzzy matching for typos and variations.
    
    Args:
        query: The search query
        threshold: Similarity threshold (0-100), default 80
        
    Returns:
        List of matching terms with similarity scores
    """
    return await _fuzzy_search_terms_impl(query, threshold)

async def smart_query(
    query: Annotated[str, Field(description="Natural language query describing what you're looking for")],
    context: Annotated[Optional[str], Field(description="Optional additional context to help with the search")] = None
) -> List[dict]:
    """
    AI-powered contextual search across the glossary using natural language.
    
    Args:
        query: Natural language query describing what you're looking for
        context: Optional additional context to help with the search
        
    Returns:
        List of relevant terms found by AI analysis
    """
    return await _smart_query_impl(query, context)

async def list_terms(
    prefix: Annotated[Optional[str], Field(description="Optional prefix to filter terms (case-insensitive)")] = None
) -> List[str]:
    """
    List available terms in the glossary with optional filtering.
    
    Args:
        prefix: Optional prefix to filter terms (case-insensitive)
        
    Returns:
        List of term names matching the filters
    """
    return await _list_terms_impl(prefix)

def initialize_plugin():
    """
    Initialize the plugin with current environment variables.
    This should be called by agentkit after environment setup.
    """
    return _initialize_plugin_impl()

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

__version__ = _module_info["version"]
__author__ = _module_info["author"]

__all__ = [
    "lookup_term",
    "batch_lookup_terms", 
    "fuzzy_search_terms",
    "smart_query",
    "list_terms",
    "initialize_plugin",
    "_module_info",
    "_module_exports"
]

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [
        lookup_term,
        batch_lookup_terms,
        fuzzy_search_terms,
        smart_query,
        list_terms
    ],
    "init_function": [initialize_plugin]
}
# =============================================================================
# END OF EXPORTS
# ============================================================================= 