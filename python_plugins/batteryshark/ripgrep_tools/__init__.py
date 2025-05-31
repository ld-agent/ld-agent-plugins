"""
Ripgrep Plugin for ld-agent

A comprehensive plugin that provides ripgrep-based code search and navigation tools
for AI agents, enabling efficient codebase exploration and analysis.
"""

import asyncio
from typing import Annotated, Optional, Dict, Any, List
from pydantic import Field

# Import implementation functions
from .implementation import (
    search_pattern_impl,
    find_symbol_impl,
    search_files_impl,
    get_file_context_impl,
    analyze_codebase_impl,
)

# Plugin metadata
_module_info = {
    "name": "Ripgrep Code Search Tools",
    "description": "Advanced code search and navigation tools using ripgrep for AI agents",
    "author": "ld-agent Team",
    "version": "1.0.0",
    "platform": "any",
    "python_requires": ">=3.9",
    "dependencies": [
        "pydantic>=2.0.0",
        "ripgrepy>=2.1.0",
        "typing-extensions>=4.0.0",
    ],
    "environment_variables": {
        "RIPGREP_PATH": {
            "description": "Path to the ripgrep binary (default: 'rg')",
            "default": "rg",
            "required": False
        },
        "RIPGREP_MAX_RESULTS": {
            "description": "Maximum number of search results to return",
            "default": "100",
            "required": False
        },
        "RIPGREP_MAX_FILESIZE": {
            "description": "Maximum file size to search (e.g., '10MB')",
            "default": "10MB",
            "required": False
        },
        "RIPGREP_TIMEOUT": {
            "description": "Timeout for search operations in seconds",
            "default": "30",
            "required": False
        },
        "RIPGREP_ALLOWED_PATHS": {
            "description": "Comma-separated list of allowed search paths (empty = all paths)",
            "default": "",
            "required": False
        },
        "RIPGREP_BLOCKED_PATTERNS": {
            "description": "Comma-separated list of patterns to block (e.g., '.git,node_modules')",
            "default": ".git,node_modules,__pycache__,.pytest_cache",
            "required": False
        }
    }
}


def search_pattern(
    pattern: Annotated[str, Field(description="Regular expression pattern to search for")],
    paths: Annotated[Optional[List[str]], Field(description="List of paths to search in (defaults to current directory)", default=None)] = None,
    file_types: Annotated[Optional[List[str]], Field(description="List of file extensions to include (e.g., ['py', 'js'])", default=None)] = None,
    context_lines: Annotated[int, Field(description="Number of lines of context to include around matches", default=3)] = 3,
    case_sensitive: Annotated[bool, Field(description="Whether search should be case sensitive", default=False)] = False,
    whole_words: Annotated[bool, Field(description="Whether to match whole words only", default=False)] = False,
    max_results: Annotated[Optional[int], Field(description="Maximum number of results to return", default=None)] = None,
) -> Dict[str, Any]:
    """
    Search for a regex pattern across files in the codebase.
    
    This function performs a comprehensive search across your codebase using ripgrep,
    returning structured results with file paths, line numbers, content, and context.
    It's optimized for AI agent consumption with detailed metadata about the search.
    
    Args:
        pattern: Regular expression pattern to search for (supports full regex syntax)
        paths: List of directory or file paths to search within. If None, searches current directory
        file_types: File extensions to limit search to (without dots, e.g., ['py', 'js', 'md'])
        context_lines: Number of lines to include before and after each match for context
        case_sensitive: Whether the search should be case sensitive (smart case used if False)
        whole_words: Whether to match only complete words (adds word boundary regex)
        max_results: Maximum number of matches to return (prevents overwhelming results)
    
    Returns:
        Dict[str, Any]: Structured search results containing:
            - query: The search parameters used
            - results: Match data with total counts, timing, and individual matches
            - error: Error message if search failed, None otherwise
            
        Each match includes:
            - file: File path where match was found
            - line: Line number (1-indexed)
            - column: Column position of match start
            - content: The actual line content
            - before_context: List of lines before the match
            - after_context: List of lines after the match
    
    Raises:
        ValueError: If pattern is empty or invalid
        PermissionError: If search paths are not accessible
    """
    return asyncio.run(search_pattern_impl(pattern, paths, file_types, context_lines, case_sensitive, whole_words, max_results))


def find_symbol(
    symbol: Annotated[str, Field(description="Name of the symbol to find")],
    symbol_type: Annotated[str, Field(description="Type of symbol: 'function', 'class', 'variable', 'constant', 'method', 'property', 'interface', 'type', 'enum', 'any'", default="any")] = "any",
    paths: Annotated[Optional[List[str]], Field(description="List of paths to search in (defaults to current directory)", default=None)] = None,
    exact_match: Annotated[bool, Field(description="Whether to match the symbol name exactly", default=False)] = False,
) -> Dict[str, Any]:
    """
    Find symbol definitions (functions, classes, variables) in the codebase.
    
    This function searches for specific code symbols using language-aware patterns
    that understand common programming language syntax for different symbol types.
    It's particularly useful for code navigation and understanding code structure.
    
    Args:
        symbol: The name of the symbol to search for (e.g., 'MyClass', 'calculate_total')
        symbol_type: The type of symbol to find. Supported types:
            - 'function': Function definitions (def, function, fn)
            - 'class': Class definitions (class, struct, interface)
            - 'variable': Variable assignments (let, var, const, =)
            - 'constant': Constant definitions (usually uppercase variables)
            - 'method': Class method definitions
            - 'property': Property definitions
            - 'interface': Interface definitions
            - 'type': Type definitions
            - 'enum': Enumeration definitions
            - 'any': Any occurrence of the symbol (broadest search)
        paths: Directories or files to search within
        exact_match: If True, matches symbol name exactly; if False, allows partial matches
    
    Returns:
        Dict[str, Any]: Symbol search results containing:
            - query: The search parameters used
            - results: Found symbols with metadata
            
        Each symbol match includes:
            - symbol_name: The searched symbol name
            - symbol_type: The type of symbol found
            - file: File path where symbol was found
            - line: Line number of the definition
            - column: Column position (if available)
            - definition: The actual line containing the definition
            - context: Surrounding lines for additional context
            - scope: Scope information (if determinable)
    
    Raises:
        ValueError: If symbol name is empty or symbol_type is invalid
    """
    return asyncio.run(find_symbol_impl(symbol, symbol_type, paths, exact_match))


def search_files(
    name_pattern: Annotated[Optional[str], Field(description="Glob pattern for file names (e.g., '*.py', 'test_*.js')", default=None)] = None,
    content_pattern: Annotated[Optional[str], Field(description="Text pattern to search within files", default=None)] = None,
    paths: Annotated[Optional[List[str]], Field(description="List of paths to search in (defaults to current directory)", default=None)] = None,
    max_size: Annotated[Optional[str], Field(description="Maximum file size (e.g., '1MB', '500KB')", default=None)] = None,
    include_stats: Annotated[bool, Field(description="Whether to include file statistics (size, type, etc.)", default=True)] = True,
) -> Dict[str, Any]:
    """
    Find files matching name patterns or containing specific content.
    
    This function provides flexible file discovery capabilities, allowing you to find
    files either by their names/paths (using glob patterns) or by their content.
    It's useful for understanding project structure and locating relevant files.
    
    Args:
        name_pattern: Glob pattern to match against file names and paths. Examples:
            - '*.py': All Python files
            - 'test_*.js': JavaScript test files
            - '**/config.*': Config files in any subdirectory
            - 'src/**/*.ts': TypeScript files in src directory tree
        content_pattern: Text or regex pattern to search for within file contents.
            If provided, only files containing this pattern will be returned.
        paths: Directories to search within. Defaults to current directory if None.
        max_size: Maximum file size to consider. Examples: '1MB', '500KB', '2GB'.
            Files larger than this will be excluded from results.
        include_stats: Whether to include file metadata (size, type, line count) in results.
    
    Returns:
        Dict[str, Any]: File search results containing:
            - query: The search parameters used
            - results: List of matching files with metadata
            
        Each file result includes:
            - path: Full path to the file
            - size: File size in bytes (if include_stats=True)
            - file_type: File extension/type
            - line_count: Number of lines in file (if scanned for content)
            - match_count: Number of content matches (if content_pattern used)
    
    Raises:
        ValueError: If both name_pattern and content_pattern are None
        OSError: If specified paths don't exist or aren't accessible
    """
    return asyncio.run(search_files_impl(name_pattern, content_pattern, paths, max_size, include_stats))


def get_file_context(
    file_path: Annotated[str, Field(description="Path to the file")],
    line_number: Annotated[int, Field(description="Line number to get context for (1-indexed)")],
    context_lines: Annotated[int, Field(description="Number of lines of context before and after", default=10)] = 10,
    include_line_numbers: Annotated[bool, Field(description="Whether to include line numbers in output", default=True)] = True,
) -> Dict[str, Any]:
    """
    Get context around a specific line in a file.
    
    This function retrieves the content around a specific line in a file, which is
    useful for understanding the context of a particular code location, examining
    errors, or getting more details about a search result.
    
    Args:
        file_path: Path to the file to read (relative or absolute)
        line_number: The target line number (1-indexed, like most editors)
        context_lines: Number of lines to include before and after the target line
        include_line_numbers: Whether to include line numbers in the returned context
    
    Returns:
        Dict[str, Any]: File context results containing:
            - query: The request parameters
            - result: Context information if successful
            - error: Error message if file couldn't be read
            
        The result includes:
            - file: Path to the file
            - target_line: The requested line number
            - content: Content of the target line
            - before_context: Lines before the target (with line numbers if requested)
            - after_context: Lines after the target (with line numbers if requested)
            - total_context_lines: Total number of lines returned
            - file_total_lines: Total lines in the file
    
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        PermissionError: If the file can't be read due to permissions
        ValueError: If line_number is less than 1
    """
    return asyncio.run(get_file_context_impl(file_path, line_number, context_lines, include_line_numbers))


def analyze_codebase(
    paths: Annotated[Optional[List[str]], Field(description="List of paths to analyze (defaults to current directory)", default=None)] = None,
    include_metrics: Annotated[bool, Field(description="Whether to include detailed metrics (may be slower)", default=True)] = True,
    file_types: Annotated[Optional[List[str]], Field(description="List of file types to focus on for analysis", default=None)] = None,
    include_language_stats: Annotated[bool, Field(description="Whether to include per-language statistics", default=True)] = True,
    max_files_to_scan: Annotated[int, Field(description="Maximum number of files to scan for detailed metrics", default=1000)] = 1000,
) -> Dict[str, Any]:
    """
    Analyze codebase structure and provide comprehensive statistics.
    
    This function performs a high-level analysis of a codebase, providing insights
    into its structure, size, complexity, and composition. It's useful for
    understanding project scope, technology stack, and overall codebase health.
    
    Args:
        paths: Directories or files to analyze. If None, analyzes current directory.
        include_metrics: Whether to calculate detailed metrics like line counts, which
            requires reading files and may be slower for large codebases.
        file_types: Specific file extensions to focus analysis on. If None, analyzes
            all common development file types.
        include_language_stats: Whether to provide per-programming-language statistics
            and breakdowns.
        max_files_to_scan: Maximum number of files to process for detailed metrics.
            Prevents performance issues on very large codebases.
    
    Returns:
        Dict[str, Any]: Comprehensive codebase analysis containing:
            - query: Analysis parameters used
            - results: Detailed statistics and metrics
            
        The results include:
            - summary: High-level totals (files, lines, size)
            - file_types: Breakdown by file extension
            - largest_files: List of largest files in the codebase
            - language_stats: Per-language statistics (if enabled)
            - directory_breakdown: Files and sizes by directory
            - recommendations: Suggestions based on the analysis
    
    Raises:
        OSError: If specified paths don't exist or aren't accessible
        MemoryError: If codebase is too large to analyze in memory
    """
    return asyncio.run(analyze_codebase_impl(paths, include_metrics, file_types, include_language_stats, max_files_to_scan))


# Export specification
_module_exports = {
    "tools": [
        search_pattern,
        find_symbol,
        search_files,
        get_file_context,
        analyze_codebase,
    ],
    "agents": [],
    "resources": [],
    "middleware": [],
    "models": [],
    "utilities": [],
} 