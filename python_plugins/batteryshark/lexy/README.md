# Lexy Glossary Plugin

AI-powered glossary search and lookup tools with exact, fuzzy, and semantic search capabilities.

## What it does

- Looks up terms in YAML glossaries with exact matching
- Searches with fuzzy matching for typos and variations  
- Performs AI-powered semantic search using natural language
- Supports batch operations for multiple term lookups
- Lists available terms with optional filtering
- Returns structured data with definitions and see-also references

## Requirements

- Python 3.10+
- `pydantic>=2.0.0`
- `rapidfuzz>=3.0.0`
- `PyYAML>=6.0.0`
- Platform: any

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEXY_GLOSSARY_PATH` | No | `glossary.yaml` | Path to YAML glossary file |
| `LEXY_LLM_MODEL` | No | `gemini-2.0-flash` | AI model for semantic search |
| `LEXY_LLM_GEMINI_API_KEY` | No | - | API key for Gemini models |
| `LEXY_LLM_OPENAI_API_KEY` | No | - | API key for OpenAI models |

## Exported Functions

### Tools

#### `lookup_term(term) -> List[dict]`
Look up a specific term with exact matching.

**Parameters:**
- `term` (str): The term to look up

**Returns:** `List[dict]` - Matching terms or suggestions if not found

#### `fuzzy_search_terms(query, threshold=80) -> List[dict]`
Search for terms using fuzzy matching for typos.

**Parameters:**
- `query` (str): The search query
- `threshold` (int, optional): Similarity threshold (0-100)

**Returns:** `List[dict]` - Matching terms with similarity scores

#### `smart_query(query, context=None) -> List[dict]`
AI-powered contextual search using natural language.

**Parameters:**
- `query` (str): Natural language query
- `context` (str, optional): Additional context

**Returns:** `List[dict]` - Relevant terms found by AI analysis

#### `batch_lookup_terms(terms) -> dict`
Look up multiple terms at once.

**Parameters:**
- `terms` (List[str]): List of terms to look up

**Returns:** `dict` - Maps each term to its lookup results

#### `list_terms(prefix=None) -> List[str]`
List available terms with optional filtering.

**Parameters:**
- `prefix` (str, optional): Prefix to filter terms

**Returns:** `List[str]` - Term names matching the filter

## Usage

```python
# Basic lookup
result = await lookup_term("MCP")

# Fuzzy search for typos
result = await fuzzy_search_terms("mcP", 70)

# AI-powered search
result = await smart_query("What is a protocol for AI models?")

# Batch operations
result = await batch_lookup_terms(["MCP", "API", "Protocol"])
```
