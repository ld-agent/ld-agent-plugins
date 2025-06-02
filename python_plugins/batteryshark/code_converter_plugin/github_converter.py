"""
GitHub Converter Implementation

This module contains the implementation logic for converting GitHub repositories
to prompt format using the GitHub API. This is a self-contained implementation
that doesn't rely on external local modules.
"""

import os
import re
import fnmatch
import base64
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import GitHub library - this will be a dependency
try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    logger.warning("GitHub library not available. GitHub functionality will be disabled.")
    GITHUB_AVAILABLE = False


class GitHubConverter:
    """Converts GitHub repositories to prompt format using the GitHub API."""
    
    def __init__(self):
        """Initialize the GitHub converter."""
        if not GITHUB_AVAILABLE:
            raise ImportError("GitHub library not available. Install PyGithub to use GitHub functionality.")
        
        # Get GitHub credentials from environment
        self.token = os.getenv('GITHUB_TOKEN')
        self.base_url = os.getenv('GITHUB_BASE_URL', 'https://api.github.com')
        self.default_org = os.getenv('GITHUB_ORG')
        
        if not self.token:
            logger.warning("No GITHUB_TOKEN found. Some operations may be limited.")
        
        # Initialize GitHub client
        try:
            if self.base_url == 'https://api.github.com':
                self.github = Github(self.token) if self.token else Github()
            else:
                self.github = Github(base_url=self.base_url, login_or_token=self.token)
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            raise
        
        # File extension mapping for syntax highlighting
        self.extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.sh': 'bash',
            '.sql': 'sql',
            '.html': 'html',
            '.xml': 'xml',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.md': 'markdown',
            '.txt': 'text',
            '.dockerfile': 'dockerfile',
            '.makefile': 'makefile'
        }
    
    def get_file_language(self, file_path: str) -> str:
        """Get the language identifier for syntax highlighting."""
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if extension in self.extension_map:
            return self.extension_map[extension]
        
        # Special cases for files without extensions
        name_lower = path_obj.name.lower()
        if name_lower == 'dockerfile':
            return 'dockerfile'
        elif name_lower in ['makefile', 'rakefile']:
            return 'makefile'
        
        return 'text'
    
    def get_repository(self, repo_name: str, org: Optional[str] = None):
        """Get a GitHub repository object."""
        try:
            org = org or self.default_org
            full_name = f"{org}/{repo_name}" if org else repo_name
            return self.github.get_repo(full_name)
        except GithubException as e:
            logger.error(f"Failed to get repository {full_name}: {e}")
            raise
    
    def get_repository_tree(self, repo, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the file tree for a repository."""
        try:
            branch = branch or repo.default_branch
            tree = repo.get_git_tree(branch, recursive=True)
            
            files = []
            for item in tree.tree:
                if item.type == 'blob':  # It's a file
                    files.append({
                        'path': item.path,
                        'sha': item.sha,
                        'size': item.size,
                        'url': item.url
                    })
            
            return files
        except GithubException as e:
            logger.error(f"Failed to get repository tree: {e}")
            raise
    
    def get_file_content(self, repo, file_path: str, branch: Optional[str] = None) -> Optional[str]:
        """Get the content of a specific file."""
        try:
            if branch:
                file_content = repo.get_contents(file_path, ref=branch)
            else:
                file_content = repo.get_contents(file_path)
            
            if file_content.content:
                # Decode base64 content
                return base64.b64decode(file_content.content).decode('utf-8', errors='ignore')
            
            return None
        except GithubException as e:
            logger.warning(f"Failed to get file content for {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error decoding file {file_path}: {e}")
            return None
    
    def filter_files(self, files: List[Dict[str, Any]], patterns: List[str]) -> List[Dict[str, Any]]:
        """Filter files based on glob patterns."""
        if not patterns:
            return files
        
        filtered = []
        for file_info in files:
            for pattern in patterns:
                if fnmatch.fnmatch(file_info['path'], pattern):
                    filtered.append(file_info)
                    break
        
        return filtered
    
    def parse_file_spec(self, spec: str) -> Tuple[str, Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """Parse a file specification with optional ranges."""
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
        elif ':' in spec and not spec.startswith('http'):
            parts = spec.rsplit(':', 1)
            if len(parts) == 2:
                file_part, range_part = parts
                if re.match(r'^\d+[-:]\d+$', range_part) or range_part.isdigit():
                    if '-' in range_part:
                        start_str, end_str = range_part.split('-', 1)
                    elif ':' in range_part:
                        start_str, end_str = range_part.split(':', 1)
                    else:
                        start_str = end_str = range_part
                    
                    try:
                        line_range = (int(start_str), int(end_str))
                    except ValueError:
                        raise ValueError(f"Invalid line range numbers: {range_part}")
                else:
                    file_part = spec
            else:
                file_part = spec
        else:
            file_part = spec
        
        return file_part, line_range, char_range
    
    def extract_content_range(self, content: str, line_range: Optional[Tuple[int, int]] = None, 
                            char_range: Optional[Tuple[int, int]] = None) -> Tuple[str, str]:
        """Extract a specific range from file content."""
        if char_range:
            start_char, end_char = char_range
            extracted = content[start_char:end_char + 1]
            range_info = f"Characters {start_char}-{end_char}"
        elif line_range:
            start_line, end_line = line_range
            lines = content.split('\n')
            extracted = '\n'.join(lines[start_line - 1:end_line])
            range_info = f"Lines {start_line}-{end_line}"
        else:
            extracted = content
            range_info = "Full file"
        
        return extracted, range_info


def _convert_github_repository_impl(repo_name: str, org: Optional[str] = None, 
                                   branch: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """Implementation function for convert_github_repository."""
    if not GITHUB_AVAILABLE:
        return "Error: GitHub functionality not available. Install PyGithub dependency."
    
    try:
        converter = GitHubConverter()
        repo = converter.get_repository(repo_name, org)
        
        # Get repository info
        repo_info = {
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description,
            'default_branch': repo.default_branch,
            'language': repo.language
        }
        
        # Get all files
        files = converter.get_repository_tree(repo, branch)
        
        # Build prompt content
        content_lines = []
        
        # Header
        content_lines.append("__")
        content_lines.append(f"Project Path: {repo_info['name']}")
        content_lines.append("")
        content_lines.append(f"GitHub Repository: {repo_info['full_name']}")
        if repo_info['description']:
            content_lines.append(f"Description: {repo_info['description']}")
        content_lines.append(f"Branch: {branch or repo_info['default_branch']}")
        content_lines.append(f"Language: {repo_info['language'] or 'Multiple'}")
        content_lines.append("")
        content_lines.append(f"Total files: {len(files)}")
        content_lines.append("")
        
        # Add each file
        processed_files = 0
        for file_info in files:
            file_path = file_info['path']
            
            # Skip very large files
            if file_info['size'] and file_info['size'] > 1024 * 1024:  # 1MB
                logger.warning(f"Skipping large file: {file_path} ({file_info['size']} bytes)")
                continue
            
            # Get file content
            content = converter.get_file_content(repo, file_path, branch)
            if content is None:
                continue
            
            # File header
            content_lines.append(f"`{file_path}`:")
            content_lines.append("")
            
            # File content in code block
            language = converter.get_file_language(file_path)
            content_lines.append(f"```{language}")
            content_lines.append(content)
            content_lines.append("```")
            content_lines.append("")
            
            processed_files += 1
        
        # Join all content
        final_content = "\n".join(content_lines)
        
        # Save to file if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.info(f"GitHub repository prompt saved to: {output_file}")
        
        logger.info(f"Processed {processed_files} files from {repo_info['full_name']}")
        return final_content
        
    except Exception as e:
        logger.error(f"Error converting GitHub repository: {str(e)}")
        return f"Error: {str(e)}"


def _convert_github_selected_files_impl(repo_name: str, file_patterns: List[str], org: Optional[str] = None,
                                       branch: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """Implementation function for convert_github_selected_files."""
    if not GITHUB_AVAILABLE:
        return "Error: GitHub functionality not available. Install PyGithub dependency."
    
    try:
        converter = GitHubConverter()
        repo = converter.get_repository(repo_name, org)
        
        # Get all files
        all_files = converter.get_repository_tree(repo, branch)
        
        # Filter files based on patterns
        selected_files = converter.filter_files(all_files, file_patterns)
        
        if not selected_files:
            return f"Warning: No files found matching patterns: {file_patterns}"
        
        # Build prompt content
        content_lines = []
        
        # Header
        content_lines.append("__")
        content_lines.append(f"Project Path: {repo.name} (Selected Files)")
        content_lines.append("")
        content_lines.append(f"GitHub Repository: {repo.full_name}")
        content_lines.append(f"Branch: {branch or repo.default_branch}")
        content_lines.append(f"Selected {len(selected_files)} files matching: {file_patterns}")
        content_lines.append("")
        
        # Add each selected file
        processed_files = 0
        for file_info in selected_files:
            file_path = file_info['path']
            
            # Get file content
            content = converter.get_file_content(repo, file_path, branch)
            if content is None:
                continue
            
            # File header
            content_lines.append(f"`{file_path}`:")
            content_lines.append("")
            
            # File content in code block
            language = converter.get_file_language(file_path)
            content_lines.append(f"```{language}")
            content_lines.append(content)
            content_lines.append("```")
            content_lines.append("")
            
            processed_files += 1
        
        # Join all content
        final_content = "\n".join(content_lines)
        
        # Save to file if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.info(f"Selected GitHub files prompt saved to: {output_file}")
        
        logger.info(f"Processed {processed_files} selected files from {repo.full_name}")
        return final_content
        
    except Exception as e:
        logger.error(f"Error converting selected GitHub files: {str(e)}")
        return f"Error: {str(e)}"


def _get_github_code_snippets_impl(repo_name: str, file_specs: List[str], org: Optional[str] = None,
                                  branch: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """Implementation function for get_github_code_snippets."""
    if not GITHUB_AVAILABLE:
        return "Error: GitHub functionality not available. Install PyGithub dependency."
    
    try:
        converter = GitHubConverter()
        repo = converter.get_repository(repo_name, org)
        
        # Process file specifications
        snippet_data = []
        for spec in file_specs:
            try:
                file_path, line_range, char_range = converter.parse_file_spec(spec)
                
                # Get file content
                content = converter.get_file_content(repo, file_path, branch)
                if content is None:
                    logger.warning(f"Could not get content for {file_path}")
                    continue
                
                # Extract range
                extracted_content, range_info = converter.extract_content_range(content, line_range, char_range)
                
                snippet_data.append({
                    'path': file_path,
                    'content': extracted_content,
                    'range_info': range_info,
                    'original_spec': spec
                })
                
            except Exception as e:
                logger.warning(f"Error processing {spec}: {e}")
                continue
        
        if not snippet_data:
            return "Warning: No valid code snippets found"
        
        # Build prompt content
        content_lines = []
        
        # Header
        content_lines.append("__")
        content_lines.append(f"Code Snippets from: {repo.full_name}")
        content_lines.append("")
        content_lines.append(f"Branch: {branch or repo.default_branch}")
        content_lines.append(f"Extracted {len(snippet_data)} code snippets:")
        content_lines.append("")
        
        # List all snippets
        for i, snippet in enumerate(snippet_data, 1):
            content_lines.append(f"{i}. {snippet['path']} ({snippet['range_info']})")
        
        content_lines.append("")
        
        # Add each snippet
        for snippet in snippet_data:
            # Snippet header
            content_lines.append(f"`{snippet['path']}` ({snippet['range_info']}):")
            content_lines.append("")
            
            # Content in code block
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
            logger.info(f"GitHub code snippets saved to: {output_file}")
        
        return final_content
        
    except Exception as e:
        logger.error(f"Error getting GitHub code snippets: {str(e)}")
        return f"Error: {str(e)}"


def _get_github_files_bulk_impl(repo_name: str, file_specs: List[str], org: Optional[str] = None,
                               branch: Optional[str] = None) -> List[Dict[str, Any]]:
    """Implementation function for get_github_files_bulk."""
    if not GITHUB_AVAILABLE:
        return [{"error": "GitHub functionality not available. Install PyGithub dependency."}]
    
    try:
        converter = GitHubConverter()
        repo = converter.get_repository(repo_name, org)
        
        # Process file specifications
        file_data = []
        for spec in file_specs:
            try:
                if '*' in spec or '?' in spec:
                    # Handle glob patterns
                    all_files = converter.get_repository_tree(repo, branch)
                    matched_files = converter.filter_files(all_files, [spec])
                    
                    for file_info in matched_files:
                        content = converter.get_file_content(repo, file_info['path'], branch)
                        if content is not None:
                            file_data.append({
                                'path': file_info['path'],
                                'content': content,
                                'size': file_info['size'],
                                'sha': file_info['sha'],
                                'language': converter.get_file_language(file_info['path']),
                                'repository': repo.full_name,
                                'branch': branch or repo.default_branch
                            })
                else:
                    # Handle specific file with optional range
                    file_path, line_range, char_range = converter.parse_file_spec(spec)
                    
                    content = converter.get_file_content(repo, file_path, branch)
                    if content is None:
                        continue
                    
                    # Extract range if specified
                    if line_range or char_range:
                        extracted_content, range_info = converter.extract_content_range(content, line_range, char_range)
                        content = extracted_content
                    
                    file_data.append({
                        'path': file_path,
                        'content': content,
                        'size': len(content.encode('utf-8')),
                        'language': converter.get_file_language(file_path),
                        'repository': repo.full_name,
                        'branch': branch or repo.default_branch,
                        'range_info': range_info if (line_range or char_range) else None
                    })
                
            except Exception as e:
                logger.warning(f"Error processing {spec}: {e}")
                continue
        
        logger.info(f"Retrieved {len(file_data)} files from {repo.full_name}")
        return file_data
        
    except Exception as e:
        logger.error(f"Error getting GitHub files bulk: {str(e)}")
        return [{"error": str(e)}] 