#!/usr/bin/env python3
"""
GitHub File Selector

Enhanced file selection capabilities for GitHub repositories, providing
sophisticated filtering, pattern matching, and content extraction tools
optimized for LLM consumption.
"""

import fnmatch
import re
import base64
from typing import List, Dict, Any, Tuple, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileSpec:
    """Specification for a file with optional range extraction."""
    path: str
    line_range: Optional[Tuple[int, int]] = None
    char_range: Optional[Tuple[int, int]] = None
    original_spec: str = ""


@dataclass
class FileResult:
    """Result of fetching and processing a file."""
    path: str
    content: str
    range_info: str
    language: str
    size: int
    sha: str
    original_spec: str = ""


class GitHubFileSelector:
    """Enhanced file selection and content extraction for GitHub repositories."""
    
    def __init__(self, github_explorer):
        """Initialize with a GitHubExplorer instance."""
        self.github_explorer = github_explorer
    
    def get_file_language(self, file_path: str) -> str:
        """Get language identifier for syntax highlighting based on file extension."""
        extension_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.jsx': 'jsx', '.tsx': 'tsx', '.java': 'java', '.c': 'c',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.h': 'c',
            '.hpp': 'cpp', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby',
            '.go': 'go', '.rs': 'rust', '.sh': 'bash', '.bash': 'bash',
            '.zsh': 'bash', '.fish': 'bash', '.ps1': 'powershell',
            '.sql': 'sql', '.html': 'html', '.htm': 'html', '.xml': 'xml',
            '.css': 'css', '.scss': 'scss', '.sass': 'sass', '.less': 'less',
            '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.toml': 'toml',
            '.ini': 'ini', '.cfg': 'ini', '.conf': 'ini', '.md': 'markdown',
            '.markdown': 'markdown', '.rst': 'rst', '.txt': 'text',
            '.log': 'text', '.dockerfile': 'dockerfile', '.makefile': 'makefile',
            '.mk': 'makefile', '.r': 'r', '.R': 'r', '.scala': 'scala',
            '.kt': 'kotlin', '.swift': 'swift', '.dart': 'dart', '.lua': 'lua',
            '.perl': 'perl', '.pl': 'perl', '.vim': 'vim'
        }
        
        # Get file extension
        path_obj = Path(file_path)
        ext = path_obj.suffix.lower()
        
        # Special cases for files without extensions
        name_lower = path_obj.name.lower()
        if name_lower in ['dockerfile', 'makefile', 'rakefile', 'gemfile']:
            return name_lower
        
        return extension_map.get(ext, 'text')
    
    def parse_file_spec(self, spec: str) -> FileSpec:
        """
        Parse a file specification with optional range.
        
        Supports formats:
        - "file.py" (entire file)
        - "file.py:10-20" (lines 10 to 20, 1-indexed)
        - "file.py@100-500" (characters 100 to 500, 0-indexed)
        
        Args:
            spec: File specification string
            
        Returns:
            FileSpec object with parsed information
        """
        line_range = None
        char_range = None
        
        # Check for character range (@start-end)
        if '@' in spec and spec.count('@') == 1:
            file_path, range_part = spec.split('@', 1)
            try:
                if '-' in range_part:
                    start, end = range_part.split('-', 1)
                    char_range = (int(start.strip()), int(end.strip()))
                else:
                    # Single character position
                    pos = int(range_part.strip())
                    char_range = (pos, pos)
            except ValueError:
                logger.warning(f"Invalid character range in spec: {spec}")
        
        # Check for line range (:start-end)
        elif ':' in spec and '@' not in spec:
            file_path, range_part = spec.rsplit(':', 1)
            try:
                if '-' in range_part:
                    start, end = range_part.split('-', 1)
                    line_range = (int(start.strip()), int(end.strip()))
                else:
                    # Single line
                    line = int(range_part.strip())
                    line_range = (line, line)
            except ValueError:
                logger.warning(f"Invalid line range in spec: {spec}")
        
        else:
            file_path = spec
        
        return FileSpec(
            path=file_path.strip(),
            line_range=line_range,
            char_range=char_range,
            original_spec=spec
        )
    
    def extract_content_range(self, 
                            content: str,
                            line_range: Optional[Tuple[int, int]] = None,
                            char_range: Optional[Tuple[int, int]] = None) -> Tuple[str, str]:
        """
        Extract content with optional range.
        
        Args:
            content: Full file content
            line_range: Optional (start_line, end_line) tuple (1-indexed)
            char_range: Optional (start_char, end_char) tuple (0-indexed)
            
        Returns:
            Tuple of (extracted_content, range_info)
        """
        if char_range:
            start_char, end_char = char_range
            extracted = content[start_char:end_char + 1]
            range_info = f"Characters {start_char}-{end_char}"
        elif line_range:
            start_line, end_line = line_range
            lines = content.split('\n')
            selected_lines = lines[start_line - 1:end_line]
            extracted = '\n'.join(selected_lines)
            range_info = f"Lines {start_line}-{end_line}"
        else:
            extracted = content
            range_info = "Full file"
        
        return extracted, range_info
    
    def resolve_file_patterns(self, 
                            patterns: List[str],
                            repo_name: str,
                            org: Optional[str] = None,
                            branch: Optional[str] = None) -> List[str]:
        """
        Resolve file patterns against a GitHub repository.
        
        Args:
            patterns: List of file paths or glob patterns
            repo_name: GitHub repository name
            org: GitHub organization name
            branch: Git branch name
            
        Returns:
            List of resolved file paths
        """
        try:
            # Get the repository tree to match against
            tree_data = self.github_explorer.get_repository_tree(
                repo_name=repo_name, 
                org=org, 
                branch=branch, 
                recursive=True
            )
            
            if not tree_data or 'tree' not in tree_data:
                logger.warning(f"Could not fetch repository tree for {repo_name}")
                return []
            
            # Extract all file paths from the tree
            all_file_paths = self._extract_file_paths_from_tree(tree_data['tree'])
            
        except Exception as e:
            logger.error(f"Error fetching repository tree: {e}")
            return []
        
        # Resolve patterns
        resolved_files = []
        
        for pattern in patterns:
            if '*' in pattern or '?' in pattern or '[' in pattern:
                # It's a glob pattern
                matches = [path for path in all_file_paths if fnmatch.fnmatch(path, pattern)]
                resolved_files.extend(matches)
            else:
                # Regular file path
                if pattern in all_file_paths:
                    resolved_files.append(pattern)
                else:
                    logger.warning(f"File not found: {pattern}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path in resolved_files:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append(file_path)
        
        return unique_files
    
    def _extract_file_paths_from_tree(self, tree_dict: Dict[str, Any], current_path: str = "") -> List[str]:
        """Extract all file paths from GitHub repository tree."""
        file_paths = []
        
        for name, info in tree_dict.items():
            item_path = f"{current_path}/{name}" if current_path else name
            
            if info.get('type') == 'blob':  # It's a file
                file_paths.append(item_path)
            elif info.get('type') == 'tree' and 'children' in info:  # It's a directory
                file_paths.extend(self._extract_file_paths_from_tree(info['children'], item_path))
        
        return file_paths
    
    def fetch_files_with_specs(self, 
                              file_specs: List[FileSpec],
                              repo_name: str,
                              org: Optional[str] = None,
                              branch: Optional[str] = None) -> List[FileResult]:
        """
        Fetch multiple files with optional ranges.
        
        Args:
            file_specs: List of file specifications
            repo_name: GitHub repository name
            org: GitHub organization name
            branch: Git branch name
            
        Returns:
            List of FileResult objects
        """
        results = []
        
        for spec in file_specs:
            try:
                # Fetch file from GitHub
                file_info = self.github_explorer.get_file(
                    repo_name=repo_name,
                    file_path=spec.path,
                    org=org,
                    branch=branch,
                    decode_content=True
                )
                
                if not file_info or not file_info.content:
                    logger.warning(f"Could not fetch file {spec.path}")
                    continue
                
                # Extract content with range if specified
                content, range_info = self.extract_content_range(
                    file_info.content,
                    spec.line_range,
                    spec.char_range
                )
                
                # Create result
                result = FileResult(
                    path=spec.path,
                    content=content,
                    range_info=range_info,
                    language=self.get_file_language(spec.path),
                    size=file_info.size,
                    sha=file_info.sha,
                    original_spec=spec.original_spec
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error fetching {spec.path}: {e}")
                continue
        
        return results
    
    def create_formatted_codeblock(self, 
                                  files: List[FileResult],
                                  repo_name: str,
                                  org: Optional[str] = None,
                                  branch: Optional[str] = None,
                                  include_metadata: bool = True) -> str:
        """
        Create a formatted codeblock from multiple files.
        
        Args:
            files: List of FileResult objects
            repo_name: Repository name for header
            org: Organization name
            branch: Branch name
            include_metadata: Whether to include file metadata
            
        Returns:
            Formatted string with all files stitched together
        """
        content_lines = []
        
        # Header
        repo_full_name = f"{org}/{repo_name}" if org else repo_name
        content_lines.append("__")
        content_lines.append(f"Repository: {repo_full_name}")
        if branch:
            content_lines.append(f"Branch: {branch}")
        content_lines.append("")
        
        if include_metadata:
            content_lines.append("Files:")
            for i, file_result in enumerate(files, 1):
                metadata = f"{i}. {file_result.path}"
                if file_result.range_info != "Full file":
                    metadata += f" ({file_result.range_info})"
                content_lines.append(metadata)
            content_lines.append("")
        
        # Add each file
        for file_result in files:
            # File header
            file_header = f"`{file_result.path}`"
            if file_result.range_info != "Full file":
                file_header += f" ({file_result.range_info})"
            content_lines.append(file_header + ":")
            content_lines.append("")
            
            # Code block
            content_lines.append(f"```{file_result.language}")
            content_lines.append(file_result.content)
            content_lines.append("```")
            content_lines.append("")
        
        return "\n".join(content_lines)


def _get_file_selector(github_explorer) -> GitHubFileSelector:
    """Get a GitHubFileSelector instance."""
    return GitHubFileSelector(github_explorer) 