# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Google Web Search",
    "description": "Web search functionality powered by Google Gemini API with grounding",
    "author": "BatteryShark",
    "version": "1.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": [
        "pydantic>=2.0.0",
        "google-genai>=0.3.0",
        "tenacity>=8.0.0",
        "requests>=2.25.0",
        "aiohttp>=3.8.0"
    ],
    "environment_variables": {
        "GOOGLE_WEBSEARCH_API_KEY": {
            "description": "Google Gemini API key for web search",
            "default": "",
            "required": True
        },
        "GOOGLE_WEBSEARCH_ENABLED": {
            "description": "Enable/disable web search functionality",
            "default": "true",
            "required": False
        },
        "GOOGLE_WEBSEARCH_MODEL": {
            "description": "Gemini model to use for web search",
            "default": "gemini-2.0-flash",
            "required": False
        },
        "GOOGLE_WEBSEARCH_MAX_REFERENCES": {
            "description": "Maximum number of references to return",
            "default": "10",
            "required": False
        },
        "GOOGLE_WEBSEARCH_TIMEOUT": {
            "description": "Request timeout in seconds",
            "default": "10",
            "required": False
        }
    }
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

from typing import Annotated, Dict, Any
from pydantic import Field

# Import implementation function
from .search_web import search_web as _search_web_impl

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

def search_web(
    search_term: Annotated[str, Field(description="The search query to process")]
) -> Dict[str, Any]:
    """
    Perform a web search using Google Gemini API with grounding.
    
    This function performs real-time web searches using Google's Gemini API
    with grounding support, providing AI-generated responses with detailed
    citations and reference extraction.
    
    Args:
        search_term: The search query to process
        
    Returns:
        Dict[str, Any]: Dictionary containing search results with status, response text,
                       references with URLs and titles, and metadata
        
    Example:
        >>> result = search_web("latest developments in AI")
        >>> print(result["data"]["response"])
        "Latest AI developments include..."
        >>> print(len(result["data"]["references"]))
        5
    """
    return _search_web_impl(search_term)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [search_web]
}
# =============================================================================
# END OF EXPORTS
# ============================================================================= 