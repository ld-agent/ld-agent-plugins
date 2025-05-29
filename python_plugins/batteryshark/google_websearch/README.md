# Google Web Search Plugin

Perform real-time web searches using Google Gemini API with grounding.

## What it does

- Searches the web using Google Gemini API with grounding support
- Returns AI-generated responses with detailed citations and references
- Automatically extracts page titles and follows redirects
- Returns structured data with status, response text, and reference metadata

## Requirements

- Python 3.10+
- `pydantic>=2.0.0`, `google-genai>=0.3.0`, `tenacity>=8.0.0`
- `requests>=2.25.0`, `aiohttp>=3.8.0`
- Platform: any

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_WEBSEARCH_API_KEY` | Yes | - | Google Gemini API key |
| `GOOGLE_WEBSEARCH_ENABLED` | No | `true` | Enable/disable web search |
| `GOOGLE_WEBSEARCH_MODEL` | No | `gemini-2.0-flash` | Gemini model to use |
| `GOOGLE_WEBSEARCH_MAX_REFERENCES` | No | `10` | Max references to return |
| `GOOGLE_WEBSEARCH_TIMEOUT` | No | `10` | Request timeout in seconds |

## Setup Google Gemini API

1. Go to [Google AI Studio](https://aistudio.google.com/) → Sign in → "Get API Key"
2. Create new API key and set `GOOGLE_WEBSEARCH_API_KEY` environment variable

## Exported Functions

### Tools

#### `search_web(search_term) -> Dict[str, Any]`
Perform a web search using Google Gemini API with grounding.

**Parameters:**
- `search_term` (str): The search query to process

**Returns:** Dictionary with search results and status

## Response Format

```json
{
  "status": "success",
  "data": {
    "response": "AI-generated answer with grounding",
    "references": [
      {"title": "Page Title", "url": "https://...", "content": "snippet"}
    ],
    "query": "original search term",
    "reference_count": 3
  }
}
```

## Usage

```python
from google_websearch import search_web

# Basic search
result = search_web("latest developments in AI")

if result["status"] == "success":
    print(result["data"]["response"])
    for ref in result["data"]["references"]:
        print(f"- {ref['title']}: {ref['url']}")
``` 