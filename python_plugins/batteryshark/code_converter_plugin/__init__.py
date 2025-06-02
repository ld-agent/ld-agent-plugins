#!/usr/bin/env python3
"""
Code Converter Plugin

This plugin provides tools for converting between directory structures and prompt formats,
including support for both local filesystems and GitHub repositories via API.
"""

# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Code Converter",
    "description": "Convert between directory structures and prompt formats with local and GitHub support",
    "author": "Code Assistant",
    "version": "1.0.0", 
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": [
        "pydantic>=2.0.0",
        "requests>=2.25.0",
        "PyGithub>=1.59.0",
        "urllib3>=1.26.0"
    ],
    "environment_variables": {
        "GITHUB_TOKEN": {
            "description": "GitHub personal access token or app token for API access",
            "default": "",
            "required": False
        },
        "GITHUB_BASE_URL": {
            "description": "GitHub API base URL (for GitHub Enterprise)",
            "default": "https://api.github.com",
            "required": False
        },
        "GITHUB_ORG": {
            "description": "Default GitHub organization to use when not specified",
            "default": "",
            "required": False
        }
    }
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

from typing import Annotated, Optional, Dict, Any, List
from pydantic import Field

# Import implementation functions
from .directory_converter import (
    _convert_directory_to_prompt_impl,
    _convert_selected_files_to_prompt_impl,
    _extract_code_snippets_impl
)
from .prompt_converter import _convert_prompt_to_directory_impl
from .github_converter import (
    _convert_github_repository_impl,
    _convert_github_selected_files_impl,
    _get_github_code_snippets_impl,
    _get_github_files_bulk_impl
)

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

def convert_directory_to_prompt(
    directory_path: Annotated[str, Field(description="Path to the directory to convert")],
    output_path: Annotated[Optional[str], Field(description="Optional path to save the output file", default=None)] = None,
    ignore_patterns: Annotated[Optional[List[str]], Field(description="Additional patterns to ignore (glob patterns)", default=None)] = None
) -> str:
    """
    Convert a directory structure into a single prompt file with all files stitched together.
    
    This function recursively scans a directory and creates a prompt file containing
    an ASCII tree of the directory structure followed by all text files formatted
    as code blocks with proper syntax highlighting.
    
    Args:
        directory_path: Path to the directory to convert
        output_path: Optional path to save the output file
        ignore_patterns: Additional patterns to ignore (similar to .gitignore)
        
    Returns:
        str: The generated prompt content
        
    Example:
        >>> content = convert_directory_to_prompt("./my_project", "output.txt")
        >>> print(len(content))
        15420
    """
    return _convert_directory_to_prompt_impl(directory_path, output_path, ignore_patterns)

def convert_selected_files_to_prompt(
    file_patterns: Annotated[List[str], Field(description="List of file paths or glob patterns to include")],
    base_dir: Annotated[str, Field(description="Base directory for resolving relative paths", default=".")] = ".",
    output_path: Annotated[Optional[str], Field(description="Optional path to save the output file", default=None)] = None
) -> str:
    """
    Convert only selected files to prompt format using file patterns or globs.
    
    This function allows selective inclusion of files based on patterns,
    useful when you only want specific files or file types included.
    
    Args:
        file_patterns: List of file paths or glob patterns (e.g., ["*.py", "README.md"])
        base_dir: Base directory for resolving relative paths
        output_path: Optional path to save the output file
        
    Returns:
        str: The generated prompt content with selected files
        
    Example:
        >>> content = convert_selected_files_to_prompt(["*.py", "README.md"], "./project")
        >>> print("Generated prompt with Python files and README")
    """
    return _convert_selected_files_to_prompt_impl(file_patterns, base_dir, output_path)

def extract_code_snippets(
    file_specs: Annotated[List[str], Field(description="List of file specifications with optional ranges (e.g., 'file.py:10-20' or 'file.py@100-500')")],
    base_dir: Annotated[str, Field(description="Base directory for resolving relative paths", default=".")] = ".",
    output_path: Annotated[Optional[str], Field(description="Optional path to save the output file", default=None)] = None
) -> str:
    """
    Extract specific code snippets from files with optional line or character ranges.
    
    This function supports extracting portions of files using line ranges or
    character ranges, perfect for focusing on specific functions or code sections.
    
    Args:
        file_specs: List of file specifications with ranges:
                   - "file.py" (entire file)
                   - "file.py:10-20" (lines 10 to 20)
                   - "file.py@100-500" (characters 100 to 500)
        base_dir: Base directory for resolving relative paths
        output_path: Optional path to save the output file
        
    Returns:
        str: The generated prompt content with code snippets
        
    Example:
        >>> snippets = extract_code_snippets(["main.py:1-50", "utils.py:100-200"])
        >>> print("Extracted specific code sections")
    """
    return _extract_code_snippets_impl(file_specs, base_dir, output_path)

def convert_prompt_to_directory(
    prompt_file_path: Annotated[str, Field(description="Path to the prompt file to convert back to directory structure")],
    output_dir_path: Annotated[Optional[str], Field(description="Path where to create the directory structure", default=None)] = None
) -> Dict[str, Any]:
    """
    Convert a prompt file back into the original directory structure and files.
    
    This function parses a prompt file created by the directory-to-prompt tools
    and recreates the original file structure, extracting files from code blocks.
    
    Args:
        prompt_file_path: Path to the prompt file to convert
        output_dir_path: Path where to create the directory structure
        
    Returns:
        Dict[str, Any]: Results including created files count and output directory
        
    Example:
        >>> result = convert_prompt_to_directory("project.txt", "./output")
        >>> print(f"Created {result['files_created']} files")
    """
    return _convert_prompt_to_directory_impl(prompt_file_path, output_dir_path)

def convert_github_repository(
    repo_name: Annotated[str, Field(description="GitHub repository name")],
    org: Annotated[Optional[str], Field(description="GitHub organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Git branch name (defaults to default branch)", default=None)] = None,
    output_path: Annotated[Optional[str], Field(description="Optional path to save the output file", default=None)] = None
) -> str:
    """
    Convert an entire GitHub repository to prompt format using the GitHub API.
    
    This function fetches all files from a GitHub repository and formats them
    into a prompt file with repository structure and file contents.
    
    Args:
        repo_name: GitHub repository name
        org: GitHub organization name
        branch: Git branch name (defaults to repository's default branch)
        output_path: Optional path to save the output file
        
    Returns:
        str: The generated prompt content with repository files
        
    Example:
        >>> content = convert_github_repository("pytorch", org="pytorch")
        >>> print("Converted PyTorch repository to prompt format")
    """
    return _convert_github_repository_impl(repo_name, org, branch, output_path)

def convert_github_selected_files(
    repo_name: Annotated[str, Field(description="GitHub repository name")],
    file_patterns: Annotated[List[str], Field(description="List of file paths or glob patterns to include")],
    org: Annotated[Optional[str], Field(description="GitHub organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Git branch name", default=None)] = None,
    output_path: Annotated[Optional[str], Field(description="Optional path to save the output file", default=None)] = None
) -> str:
    """
    Convert selected files from a GitHub repository to prompt format.
    
    This function allows selective inclusion of files from a GitHub repository
    based on patterns, useful for large repositories where you only need specific files.
    
    Args:
        repo_name: GitHub repository name
        file_patterns: List of file paths or glob patterns (e.g., ["*.py", "README.md"])
        org: GitHub organization name
        branch: Git branch name
        output_path: Optional path to save the output file
        
    Returns:
        str: The generated prompt content with selected repository files
        
    Example:
        >>> content = convert_github_selected_files("repo", ["*.py"], org="myorg")
        >>> print("Converted Python files from GitHub repository")
    """
    return _convert_github_selected_files_impl(repo_name, file_patterns, org, branch, output_path)

def get_github_code_snippets(
    repo_name: Annotated[str, Field(description="GitHub repository name")],
    file_specs: Annotated[List[str], Field(description="List of file specifications with optional ranges")],
    org: Annotated[Optional[str], Field(description="GitHub organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Git branch name", default=None)] = None,
    output_path: Annotated[Optional[str], Field(description="Optional path to save the output file", default=None)] = None
) -> str:
    """
    Extract code snippets from GitHub repository files with optional ranges.
    
    This function fetches specific portions of files from a GitHub repository,
    supporting line and character ranges for precise code extraction.
    
    Args:
        repo_name: GitHub repository name
        file_specs: List of file specifications with ranges (same format as extract_code_snippets)
        org: GitHub organization name
        branch: Git branch name
        output_path: Optional path to save the output file
        
    Returns:
        str: The generated prompt content with code snippets from GitHub
        
    Example:
        >>> snippets = get_github_code_snippets("repo", ["main.py:1-50"], org="myorg")
        >>> print("Extracted code snippets from GitHub repository")
    """
    return _get_github_code_snippets_impl(repo_name, file_specs, org, branch, output_path)

def get_github_files_bulk(
    repo_name: Annotated[str, Field(description="GitHub repository name")],
    file_specs: Annotated[List[str], Field(description="List of file specifications with optional ranges")],
    org: Annotated[Optional[str], Field(description="GitHub organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Git branch name", default=None)] = None
) -> List[Dict[str, Any]]:
    """
    Fetch multiple files from GitHub repository and return as structured data.
    
    This function is perfect for MCP tools that need structured file data rather
    than formatted text. Returns an array of file objects with metadata.
    
    Args:
        repo_name: GitHub repository name
        file_specs: List of file specifications with optional ranges
        org: GitHub organization name
        branch: Git branch name
        
    Returns:
        List[Dict[str, Any]]: List of file objects with path, content, metadata
        
    Example:
        >>> files = get_github_files_bulk("repo", ["*.py"], org="myorg")
        >>> for file in files:
        ...     print(f"File: {file['path']}, Size: {file['size']}")
    """
    return _get_github_files_bulk_impl(repo_name, file_specs, org, branch)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [
        convert_directory_to_prompt,
        convert_selected_files_to_prompt,
        extract_code_snippets,
        convert_prompt_to_directory,
        convert_github_repository,
        convert_github_selected_files,
        get_github_code_snippets,
        get_github_files_bulk
    ]
}
# =============================================================================
# END OF EXPORTS
# ============================================================================= 