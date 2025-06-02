"""
Directory Converter Implementation

This module contains the implementation logic for converting directory structures
to prompt format and extracting code snippets from local files.
"""

import os
import sys
import glob
import re
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DirectoryToPrompt:
    """Converts directory structure to a prompt file format."""
    
    def __init__(self, ignore_patterns: List[str] = None):
        """
        Initialize the converter.
        
        Args:
            ignore_patterns: List of patterns to ignore (similar to .gitignore)
        """
        self.ignore_patterns = ignore_patterns or [
            '.git*',
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '.DS_Store',
            'node_modules',
            '.env',
            '*.log',
            '.vscode',
            '.idea',
            '*.tmp',
            '*.temp'
        ]
        
        # Common text file extensions
        self.text_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx',
            '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.sh', '.bash', '.zsh',
            '.fish', '.ps1', '.sql', '.html', '.htm', '.xml', '.css', '.scss', '.sass',
            '.less', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.md', '.markdown', '.rst', '.txt', '.log', '.dockerfile', '.makefile',
            '.r', '.R', '.scala', '.kt', '.swift', '.dart', '.lua', '.perl', '.pl',
            '.vim', '.gitignore', '.gitattributes', '.editorconfig', '.env.example'
        }
        
        # File extension to code block language mapping
        self.extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'bash',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.html': 'html',
            '.htm': 'html',
            '.xml': 'xml',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
            '.md': 'md',
            '.markdown': 'markdown',
            '.rst': 'rst',
            '.txt': 'txt',
            '.log': 'text',
            '.dockerfile': 'dockerfile',
            '.makefile': 'makefile',
            '.r': 'r',
            '.R': 'r',
            '.scala': 'scala',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.dart': 'dart',
            '.lua': 'lua',
            '.perl': 'perl',
            '.pl': 'perl',
            '.vim': 'vim',
        }
    
    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on ignore patterns."""
        path_str = str(path)
        name = path.name
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path_str, pattern):
                return True
        
        return False
    
    def is_text_file(self, file_path: Path) -> bool:
        """Check if a file is likely a text file."""
        # Check by extension first
        if file_path.suffix.lower() in self.text_extensions:
            return True
        
        # Files without extensions that are commonly text
        if not file_path.suffix and file_path.name.lower() in [
            'dockerfile', 'makefile', 'rakefile', 'gemfile', 'readme',
            'license', 'changelog', 'contributing', 'authors'
        ]:
            return True
        
        # Try to read the first few bytes to detect binary files
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:  # Binary files often contain null bytes
                    return False
                # Try to decode as UTF-8
                chunk.decode('utf-8')
                return True
        except (UnicodeDecodeError, PermissionError, OSError):
            return False
    
    def get_file_language(self, file_path: Path) -> str:
        """Get the language identifier for syntax highlighting."""
        extension = file_path.suffix.lower()
        
        # Check extension mapping
        if extension in self.extension_map:
            return self.extension_map[extension]
        
        # Special cases for files without extensions
        name_lower = file_path.name.lower()
        if name_lower in ['dockerfile']:
            return 'dockerfile'
        elif name_lower in ['makefile', 'rakefile']:
            return 'makefile'
        elif name_lower in ['gemfile']:
            return 'ruby'
        
        return 'txt'
    
    def parse_line_range_spec(self, spec: str) -> Tuple[Path, Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """
        Parse a file specification with optional line or character ranges.
        
        Supported formats:
        - "path/to/file.py" - entire file
        - "path/to/file.py:10-20" - lines 10 to 20
        - "path/to/file.py:10:20" - lines 10 to 20 (alternative syntax)
        - "path/to/file.py@100-500" - characters 100 to 500
        - "path/to/file.py@100:500" - characters 100 to 500 (alternative syntax)
        
        Args:
            spec: File specification string
            
        Returns:
            Tuple of (file_path, line_range, char_range)
            line_range and char_range are (start, end) tuples or None
        """
        line_range = None
        char_range = None
        
        # Check for character range (@)
        if '@' in spec:
            file_part, range_part = spec.rsplit('@', 1)
            if '-' in range_part:
                start_str, end_str = range_part.split('-', 1)
            elif ':' in range_part:
                start_str, end_str = range_part.split(':', 1)
            else:
                raise ValueError(f"Invalid character range format: {range_part}")
            
            try:
                char_range = (int(start_str), int(end_str))
            except ValueError:
                raise ValueError(f"Invalid character range numbers: {range_part}")
        
        # Check for line range (:)
        elif ':' in spec and not spec.startswith('/') and '://' not in spec:
            # Split from the right to handle Windows paths like C:\path\file.py:10-20
            parts = spec.rsplit(':', 1)
            if len(parts) == 2:
                file_part, range_part = parts
                # Check if this looks like a line range (contains digits or range syntax)
                if re.match(r'^\d+[-:]\d+$', range_part) or range_part.isdigit():
                    if '-' in range_part:
                        start_str, end_str = range_part.split('-', 1)
                    elif ':' in range_part:
                        start_str, end_str = range_part.split(':', 1)
                    else:
                        # Single line number
                        start_str = end_str = range_part
                    
                    try:
                        line_range = (int(start_str), int(end_str))
                    except ValueError:
                        raise ValueError(f"Invalid line range numbers: {range_part}")
                else:
                    # Not a range, treat as regular file path
                    file_part = spec
            else:
                file_part = spec
        else:
            file_part = spec
        
        return Path(file_part), line_range, char_range
    
    def extract_file_content(self, 
                           file_path: Path, 
                           line_range: Optional[Tuple[int, int]] = None,
                           char_range: Optional[Tuple[int, int]] = None) -> Tuple[str, str]:
        """
        Extract content from a file with optional line or character range.
        
        Args:
            file_path: Path to the file
            line_range: Optional (start_line, end_line) tuple (1-indexed)
            char_range: Optional (start_char, end_char) tuple (0-indexed)
            
        Returns:
            Tuple of (content, range_info)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                full_content = f.read()
        except Exception as e:
            return f"# Error reading file: {e}", "Error"
        
        if char_range:
            start_char, end_char = char_range
            content = full_content[start_char:end_char + 1]
            range_info = f"Characters {start_char}-{end_char}"
        elif line_range:
            start_line, end_line = line_range
            lines = full_content.split('\n')
            # Convert to 0-indexed for slicing
            selected_lines = lines[start_line - 1:end_line]
            content = '\n'.join(selected_lines)
            range_info = f"Lines {start_line}-{end_line}"
        else:
            content = full_content
            range_info = "Full file"
        
        return content, range_info
    
    def build_tree_structure(self, root_path: Path) -> Dict[str, Any]:
        """Build a nested dictionary representing the directory structure."""
        def _build_tree(path: Path, level: int = 0) -> Dict[str, Any]:
            tree = {
                'name': path.name,
                'path': path,
                'is_file': path.is_file(),
                'children': []
            }
            
            if path.is_dir() and not self.should_ignore(path):
                try:
                    for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        if not self.should_ignore(child):
                            tree['children'].append(_build_tree(child, level + 1))
                except PermissionError:
                    pass  # Skip directories we can't read
            
            return tree
        
        return _build_tree(root_path)
    
    def generate_ascii_tree(self, tree: Dict[str, Any], prefix: str = "", is_last: bool = True) -> List[str]:
        """Generate ASCII tree representation of the directory structure."""
        lines = []
        
        if prefix == "":  # Root node
            lines.append(tree['name'])
        else:
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{tree['name']}")
        
        children = [child for child in tree['children'] if not child['is_file']] + \
                  [child for child in tree['children'] if child['is_file']]
        
        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            if prefix == "":
                child_prefix = ""
            else:
                child_prefix = prefix + ("    " if is_last else "│   ")
            
            child_lines = self.generate_ascii_tree(child, child_prefix, is_last_child)
            lines.extend(child_lines)
        
        return lines
    
    def collect_files(self, tree: Dict[str, Any]) -> List[Path]:
        """Collect all text files from the tree structure."""
        files = []
        
        def _collect_recursive(node: Dict[str, Any]):
            if node['is_file']:
                file_path = node['path']
                if self.is_text_file(file_path):
                    files.append(file_path)
            else:
                for child in node['children']:
                    _collect_recursive(child)
        
        _collect_recursive(tree)
        return sorted(files)
    
    def read_file_content(self, file_path: Path) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"# Error reading file: {e}"


def _convert_directory_to_prompt_impl(directory_path: str, output_path: Optional[str] = None, ignore_patterns: Optional[List[str]] = None) -> str:
    """
    Implementation function for convert_directory_to_prompt.
    
    Args:
        directory_path: Path to the directory to convert
        output_path: Optional path to save the output
        ignore_patterns: Additional patterns to ignore
        
    Returns:
        The generated prompt content
    """
    try:
        root_path = Path(directory_path).resolve()
        
        if not root_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return f"Error: Directory not found: {directory_path}"
        
        if not root_path.is_dir():
            logger.error(f"Path is not a directory: {directory_path}")
            return f"Error: Path is not a directory: {directory_path}"
        
        # Initialize converter
        converter = DirectoryToPrompt(ignore_patterns)
        
        # Build tree structure
        tree = converter.build_tree_structure(root_path)
        
        # Generate ASCII tree
        ascii_lines = converter.generate_ascii_tree(tree)
        
        # Collect all text files
        files = converter.collect_files(tree)
        
        # Build the prompt content
        content_lines = []
        
        # Header
        content_lines.append("__")
        content_lines.append(f"Project Path: {root_path.name}")
        content_lines.append("")
        content_lines.append("Source Tree:")
        content_lines.append("")
        content_lines.append("```txt")
        content_lines.extend(ascii_lines)
        content_lines.append("")
        content_lines.append("```")
        content_lines.append("")
        
        # Add each file
        for file_path in files:
            # Get relative path from root
            try:
                rel_path = file_path.relative_to(root_path)
            except ValueError:
                rel_path = file_path
            
            # File header
            content_lines.append(f"`{rel_path}`:")
            content_lines.append("")
            
            # File content in code block
            language = converter.get_file_language(file_path)
            content_lines.append(f"```{language}")
            
            file_content = converter.read_file_content(file_path)
            content_lines.append(file_content)
            
            content_lines.append("```")
            content_lines.append("")
        
        # Join all content
        final_content = "\n".join(content_lines)
        
        # Save to file if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.info(f"Prompt saved to: {output_file}")
        
        return final_content
        
    except Exception as e:
        logger.error(f"Error converting directory to prompt: {str(e)}")
        return f"Error: {str(e)}"


def _convert_selected_files_to_prompt_impl(file_patterns: List[str], base_dir: str = ".", output_path: Optional[str] = None) -> str:
    """
    Implementation function for convert_selected_files_to_prompt.
    
    Args:
        file_patterns: List of file paths or glob patterns to include
        base_dir: Base directory for resolving relative paths
        output_path: Optional path to save the output
        
    Returns:
        The generated prompt content
    """
    try:
        base_path = Path(base_dir).resolve()
        
        if not base_path.exists():
            logger.error(f"Base directory not found: {base_dir}")
            return f"Error: Base directory not found: {base_dir}"
        
        # Initialize converter
        converter = DirectoryToPrompt()
        
        # Resolve file patterns to actual file paths
        selected_files = []
        for pattern in file_patterns:
            if '*' in pattern or '?' in pattern or '[' in pattern:
                # It's a glob pattern
                matches = glob.glob(str(base_path / pattern), recursive=True)
                selected_files.extend([Path(match) for match in matches])
            else:
                # Regular file path
                file_path = base_path / pattern
                if file_path.exists() and file_path.is_file():
                    selected_files.append(file_path)
        
        # Filter for text files and remove duplicates
        text_files = []
        seen = set()
        for file_path in selected_files:
            if file_path not in seen and converter.is_text_file(file_path):
                seen.add(file_path)
                text_files.append(file_path)
        
        if not text_files:
            logger.warning("No valid files found matching the specified patterns")
            return "Warning: No valid files found matching the specified patterns"
        
        # Build the prompt content
        content_lines = []
        
        # Header
        content_lines.append("__")
        content_lines.append(f"Project Path: {base_path.name} (Selected Files)")
        content_lines.append("")
        content_lines.append(f"Selected {len(text_files)} files:")
        content_lines.append("")
        
        # List selected files
        for file_path in text_files:
            try:
                rel_path = file_path.relative_to(base_path)
            except ValueError:
                rel_path = file_path
            content_lines.append(f"- {rel_path}")
        
        content_lines.append("")
        
        # Add each file
        for file_path in text_files:
            # Get relative path from base
            try:
                rel_path = file_path.relative_to(base_path)
            except ValueError:
                rel_path = file_path
            
            # File header
            content_lines.append(f"`{rel_path}`:")
            content_lines.append("")
            
            # File content in code block
            language = converter.get_file_language(file_path)
            content_lines.append(f"```{language}")
            
            file_content = converter.read_file_content(file_path)
            content_lines.append(file_content)
            
            content_lines.append("```")
            content_lines.append("")
        
        # Join all content
        final_content = "\n".join(content_lines)
        
        # Save to file if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.info(f"Prompt saved to: {output_file}")
        
        return final_content
        
    except Exception as e:
        logger.error(f"Error converting selected files to prompt: {str(e)}")
        return f"Error: {str(e)}"


def _extract_code_snippets_impl(file_specs: List[str], base_dir: str = ".", output_path: Optional[str] = None) -> str:
    """
    Implementation function for extract_code_snippets.
    
    Args:
        file_specs: List of file specifications with optional ranges
        base_dir: Base directory for resolving relative paths
        output_path: Optional path to save the output
        
    Returns:
        The generated prompt content with code snippets
    """
    try:
        base_path = Path(base_dir).resolve()
        
        if not base_path.exists():
            logger.error(f"Base directory not found: {base_dir}")
            return f"Error: Base directory not found: {base_dir}"
        
        # Initialize converter
        converter = DirectoryToPrompt()
        
        # Parse file specifications
        snippet_data = []
        for spec in file_specs:
            try:
                file_path, line_range, char_range = converter.parse_line_range_spec(spec)
                
                # Resolve relative paths
                if not file_path.is_absolute():
                    file_path = base_path / file_path
                
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                if not converter.is_text_file(file_path):
                    logger.warning(f"Skipping binary file: {file_path}")
                    continue
                
                # Extract content
                content, range_info = converter.extract_file_content(file_path, line_range, char_range)
                
                snippet_data.append({
                    'path': file_path,
                    'content': content,
                    'range_info': range_info,
                    'original_spec': spec
                })
                
            except Exception as e:
                logger.warning(f"Error processing {spec}: {e}")
                continue
        
        if not snippet_data:
            logger.warning("No valid code snippets found")
            return "Warning: No valid code snippets found"
        
        # Build the prompt content
        content_lines = []
        
        # Header
        content_lines.append("__")
        content_lines.append(f"Code Snippets from: {base_path.name}")
        content_lines.append("")
        content_lines.append(f"Extracted {len(snippet_data)} code snippets:")
        content_lines.append("")
        
        # List all snippets
        for i, snippet in enumerate(snippet_data, 1):
            try:
                rel_path = snippet['path'].relative_to(base_path)
            except ValueError:
                rel_path = snippet['path']
            content_lines.append(f"{i}. {rel_path} ({snippet['range_info']})")
        
        content_lines.append("")
        
        # Add each snippet
        for snippet in snippet_data:
            # Get relative path from base
            try:
                rel_path = snippet['path'].relative_to(base_path)
            except ValueError:
                rel_path = snippet['path']
            
            # Snippet header
            content_lines.append(f"`{rel_path}` ({snippet['range_info']}):")
            content_lines.append("")
            
            # File content in code block
            language = converter.get_file_language(snippet['path'])
            content_lines.append(f"```{language}")
            
            content_lines.append(snippet['content'])
            
            content_lines.append("```")
            content_lines.append("")
        
        # Join all content
        final_content = "\n".join(content_lines)
        
        # Save to file if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.info(f"Code snippets saved to: {output_file}")
        
        return final_content
        
    except Exception as e:
        logger.error(f"Error extracting code snippets: {str(e)}")
        return f"Error: {str(e)}" 