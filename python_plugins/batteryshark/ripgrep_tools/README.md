# Ripgrep Plugin for ld-agent

A comprehensive plugin that provides ripgrep-based code search and navigation tools for AI agents, enabling efficient codebase exploration and analysis.

## 🎯 Overview

This plugin leverages the power of [ripgrep](https://github.com/BurntSushi/ripgrep) - the fastest grep-like tool available - to provide AI agents with sophisticated code search capabilities. It offers structured search results optimized for AI consumption and supports various search patterns including regex, symbol lookup, file discovery, and codebase analysis.

## ✨ Features

### Core Search Tools
- **Pattern Search**: Search for regex patterns across files with context
- **Symbol Search**: Find function definitions, class declarations, variables, etc.
- **File Discovery**: Find files by name patterns or content
- **Context Extraction**: Get code context around specific locations
- **Codebase Analysis**: High-level statistics and structure analysis

### Agent-Optimized Features
- **Structured Output**: JSON results perfect for AI agent consumption
- **Async Operations**: Non-blocking searches for better performance
- **Smart Filtering**: Configurable file type and pattern filtering
- **Security Controls**: Path restrictions and pattern blocking
- **Performance Limits**: Configurable timeouts and result limits

## 📋 Installation

### Prerequisites

1. **Python 3.9+** installed
2. **ripgrep** installed and available in PATH

Install ripgrep:
```bash
# macOS
brew install ripgrep

# Ubuntu/Debian  
sudo apt install ripgrep

# Windows (Chocolatey)
choco install ripgrep

# Or download from: https://github.com/BurntSushi/ripgrep/releases
```

### Plugin Dependencies

The plugin will automatically install these dependencies:
- `pydantic>=2.0.0`
- `ripgrepy>=2.1.0` (optional, falls back to CLI if not available)
- `typing-extensions>=4.0.0`

## ⚙️ Configuration

The plugin is configured via environment variables:

### Required Environment Variables
None - all variables have sensible defaults.

### Optional Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `RIPGREP_PATH` | Path to ripgrep binary | `rg` | `/usr/local/bin/rg` |
| `RIPGREP_MAX_RESULTS` | Maximum search results | `100` | `50` |
| `RIPGREP_MAX_FILESIZE` | Maximum file size to search | `10MB` | `5MB` |
| `RIPGREP_TIMEOUT` | Search timeout in seconds | `30` | `60` |
| `RIPGREP_ALLOWED_PATHS` | Allowed search paths (comma-separated) | *(all paths)* | `/workspace,/src` |
| `RIPGREP_BLOCKED_PATTERNS` | Blocked path patterns | `.git,node_modules,__pycache__,.pytest_cache` | `.git,target,dist` |

### Example Configuration

```bash
export RIPGREP_MAX_RESULTS=50
export RIPGREP_ALLOWED_PATHS="/workspace,/home/user/projects"
export RIPGREP_BLOCKED_PATTERNS=".git,node_modules,target,dist,build"
```

## 🛠️ Available Tools

### 1. `search_pattern`

Search for regex patterns across files with context.

**Parameters:**
- `pattern` (str, required): Regular expression pattern to search for
- `paths` (List[str], optional): Paths to search in (defaults to current directory)
- `file_types` (List[str], optional): File extensions to include (e.g., `['py', 'js']`)
- `context_lines` (int, default=3): Lines of context around matches
- `case_sensitive` (bool, default=False): Whether search is case sensitive
- `whole_words` (bool, default=False): Match whole words only
- `max_results` (int, optional): Maximum results to return

**Example:**
```python
result = search_pattern(
    pattern=r"function\s+\w+\s*\(",
    paths=["src/"],
    file_types=["js", "ts"],
    context_lines=5
)
```

### 2. `find_symbol`

Find specific symbols (functions, classes, variables) in code.

**Parameters:**
- `symbol` (str, required): Symbol name to find
- `symbol_type` (str, default="any"): Type of symbol (`function`, `class`, `variable`, `any`, etc.)
- `paths` (List[str], optional): Paths to search in
- `exact_match` (bool, default=False): Whether to match symbol name exactly

**Example:**
```python
result = find_symbol(
    symbol="UserService", 
    symbol_type="class",
    exact_match=True
)
```

### 3. `search_files`

Find files by name patterns or content.

**Parameters:**
- `name_pattern` (str, optional): Glob pattern for file names (e.g., `*.py`)
- `content_pattern` (str, optional): Text pattern to search within files
- `paths` (List[str], optional): Paths to search in
- `max_size` (str, optional): Maximum file size (e.g., `1MB`)
- `include_stats` (bool, default=True): Include file metadata

**Example:**
```python
result = search_files(
    name_pattern="test_*.py",
    content_pattern="async def",
    max_size="1MB"
)
```

### 4. `get_file_context`

Get context around a specific line in a file.

**Parameters:**
- `file_path` (str, required): Path to the file
- `line_number` (int, required): Line number (1-indexed)
- `context_lines` (int, default=10): Lines of context before and after
- `include_line_numbers` (bool, default=True): Include line numbers in output

**Example:**
```python
result = get_file_context(
    file_path="src/main.py",
    line_number=42,
    context_lines=15
)
```

### 5. `analyze_codebase`

Analyze codebase structure and provide statistics.

**Parameters:**
- `paths` (List[str], optional): Paths to analyze
- `include_metrics` (bool, default=True): Include detailed metrics
- `file_types` (List[str], optional): File types to focus on
- `include_language_stats` (bool, default=True): Include per-language stats
- `max_files_to_scan` (int, default=1000): Maximum files for detailed metrics

**Example:**
```python
result = analyze_codebase(
    paths=["src/", "lib/"],
    include_metrics=True,
    file_types=["py", "js", "ts"]
)
```

## 📤 Return Values

All tools return structured dictionaries with consistent formats:

```python
{
    "query": {
        # Parameters used for the search
    },
    "results": {
        # Search results and metadata
    },
    "error": None  # or error message if search failed
}
```

## 🔒 Security Features

### Path Restrictions
- Configure `RIPGREP_ALLOWED_PATHS` to limit searchable directories
- Prevents agents from accessing sensitive areas of the file system

### Pattern Blocking
- Configure `RIPGREP_BLOCKED_PATTERNS` to skip sensitive directories
- Default blocks `.git`, `node_modules`, `__pycache__`, etc.

### Performance Limits
- Configurable result limits prevent overwhelming responses
- File size limits prevent processing huge files
- Timeout controls prevent long-running searches

## 🚨 Error Handling

The plugin handles various error conditions gracefully:

- **File not found**: Returns structured error message
- **Permission denied**: Returns access denied error
- **Invalid patterns**: Returns pattern validation error
- **Path restrictions**: Returns path not allowed error
- **Timeout**: Returns timeout error with partial results

All errors are returned in the same structured format with descriptive messages.

## 🧪 Testing

The plugin can be tested manually:

```python
from ripgrep_plugin import search_pattern, find_symbol

# Test pattern search
result = search_pattern("def test_", file_types=["py"])
print(f"Found {result['results']['total_matches']} test functions")

# Test symbol search
result = find_symbol("main", symbol_type="function")
print(f"Found {result['results']['total_matches']} main functions")
```

## 📈 Performance

- **Speed**: Leverages ripgrep's rust-based performance (10-100x faster than grep)
- **Memory**: Efficient streaming for large codebases
- **Scalability**: Configurable limits prevent resource exhaustion
- **Concurrency**: Async design supports multiple concurrent requests

## 🔧 Troubleshooting

### Common Issues

1. **"ripgrep not found"**
   - Install ripgrep: `brew install ripgrep` (macOS)
   - Set custom path: `export RIPGREP_PATH="/path/to/rg"`

2. **"Path not allowed"**
   - Check `RIPGREP_ALLOWED_PATHS` configuration
   - Ensure the path is within allowed directories

3. **Empty results**
   - Verify the pattern syntax (uses regex)
   - Check file types are correct
   - Try broader search terms

4. **Performance issues**
   - Reduce `RIPGREP_MAX_RESULTS` limit
   - Use more specific file types
   - Add more blocked patterns

### Debug Mode

Set logging level to debug for detailed output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔗 Integration Examples

### Basic Usage
```python
from ripgrep_plugin import search_pattern

# Search for Python function definitions
result = search_pattern(
    pattern=r"def\s+\w+\s*\(",
    file_types=["py"],
    context_lines=2
)

for match in result["results"]["matches"]:
    print(f"{match['file']}:{match['line']}: {match['content']}")
```

### Advanced Usage
```python
from ripgrep_plugin import find_symbol, analyze_codebase

# Find all class definitions
classes = find_symbol("", symbol_type="class")
print(f"Found {len(classes['results']['matches'])} classes")

# Analyze project structure
stats = analyze_codebase(include_metrics=True)
print(f"Project has {stats['results']['summary']['total_files']} files")
```

## 📄 License

This plugin follows the same license as the main ld-agent project.

## 🤝 Contributing

1. Ensure ripgrep is installed and working
2. Test all functions with various inputs
3. Verify error handling works correctly
4. Check that environment variables are respected
5. Validate structured output format

## 🙏 Acknowledgments

- [ripgrep](https://github.com/BurntSushi/ripgrep) by Andrew Gallant
- [ripgrepy](https://github.com/securisec/ripgrepy) Python wrapper
- ld-agent plugin specification contributors 