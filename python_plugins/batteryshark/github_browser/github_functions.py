import os
import logging
import subprocess
import configparser
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import asdict

# Import the existing GitHubExplorer and new file selector
from .github_explorer import GitHubExplorer, FileInfo, RepositoryInfo
from .file_selector import GitHubFileSelector, FileSpec, FileResult, _get_file_selector

# Global explorer instance
_github_explorer = None
_file_selector = None
_initialized = False

logger = logging.getLogger(__name__)

def _initialize_plugin_impl() -> None:
    """Initialize the GitHub Browser plugin with current environment variables."""
    global _initialized, _github_explorer, _file_selector
    _initialized = False  # Force re-initialization
    _github_explorer = None  # Reset explorer
    _file_selector = None  # Reset file selector
    _ensure_initialized()
    logger.info("GitHub Browser Plugin initialized")

def _ensure_initialized():
    """Ensure the plugin is properly initialized."""
    global _initialized
    if not _initialized:
        _get_explorer()  # This will trigger initialization
        _initialized = True

def _get_explorer() -> GitHubExplorer:
    """Get or create the GitHub Explorer instance."""
    global _github_explorer
    if _github_explorer is None:
        # Don't pass token directly - let the new auth logic handle it
        base_url = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
        org = os.getenv("GITHUB_ORG")
        app_id = os.getenv("GITHUB_APP_ID")
        private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
        auth_preference = os.getenv("GITHUB_AUTH_PREFERENCE", "auto")
        
        try:
            _github_explorer = GitHubExplorer(
                base_url=base_url,
                org=org,
                app_id=app_id,
                private_key_path=private_key_path,
                auth_preference=auth_preference
            )
        except Exception as e:
            logger.error(f"Failed to initialize GitHub Explorer: {e}")
            raise ValueError(f"GitHub Explorer initialization failed: {e}")
    
    return _github_explorer

def _get_file_selector_instance() -> GitHubFileSelector:
    """Get or create the file selector instance."""
    global _file_selector
    if _file_selector is None:
        explorer = _get_explorer()
        _file_selector = _get_file_selector(explorer)
    return _file_selector

def _convert_file_info_to_dict(file_info: FileInfo) -> Dict[str, Any]:
    """Convert FileInfo dataclass to dictionary."""
    return asdict(file_info)

def _convert_repo_info_to_dict(repo_info: RepositoryInfo) -> Dict[str, Any]:
    """Convert RepositoryInfo dataclass to dictionary."""
    data = asdict(repo_info)
    # Convert datetime objects to ISO strings
    if 'created_at' in data and data['created_at']:
        data['created_at'] = data['created_at'].isoformat()
    if 'updated_at' in data and data['updated_at']:
        data['updated_at'] = data['updated_at'].isoformat()
    return data

def _convert_file_result_to_dict(file_result: FileResult) -> Dict[str, Any]:
    """Convert FileResult dataclass to dictionary."""
    return asdict(file_result)

# =============================================================================
# ORIGINAL GITHUB BROWSER FUNCTIONS
# =============================================================================

def _search_files_impl(
    query: str,
    repo: Optional[str] = None,
    org: Optional[str] = None,
    path: Optional[str] = None,
    extension: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Implementation function for search_files."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        file_infos = explorer.search_files(
            query=query,
            repo=repo,
            org=org,
            path=path,
            extension=extension,
            limit=limit
        )
        
        return [_convert_file_info_to_dict(file_info) for file_info in file_infos]
        
    except Exception as e:
        logger.error(f"Error in search_files: {e}")
        return []

def _search_content_impl(
    query: str,
    repo: Optional[str] = None,
    org: Optional[str] = None,
    path: Optional[str] = None,
    extension: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for search_content."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.search_content(
            query=query,
            repo=repo,
            org=org,
            path=path,
            extension=extension,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in search_content: {e}")
        return []

def _list_repositories_impl(
    org: Optional[str] = None,
    type: str = 'all',
    sort: str = 'updated',
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for list_repositories."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        repo_infos = explorer.list_repositories(
            org=org,
            type=type,
            sort=sort,
            limit=limit
        )
        
        return [_convert_repo_info_to_dict(repo_info) for repo_info in repo_infos]
        
    except Exception as e:
        logger.error(f"Error in list_repositories: {str(e)}")
        return []

def _get_repository_info_impl(
    repo_name: str,
    org: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Implementation function for get_repository_info."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        repo_info = explorer.get_repository_info(repo_name=repo_name, org=org)
        
        if repo_info:
            return _convert_repo_info_to_dict(repo_info)
        return None
        
    except Exception as e:
        logger.error(f"Error in get_repository_info: {e}")
        return None

def _get_contributors_impl(
    repo_name: str,
    org: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for get_contributors."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.get_contributors(
            repo_name=repo_name,
            org=org,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in get_contributors: {e}")
        return []

def _get_repository_tree_impl(
    repo_name: str,
    org: Optional[str] = None,
    branch: Optional[str] = None,
    recursive: bool = True
) -> Dict[str, Any]:
    """Implementation function for get_repository_tree."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.get_repository_tree(
            repo_name=repo_name,
            org=org,
            branch=branch,
            recursive=recursive
        )
        
    except Exception as e:
        logger.error(f"Error in get_repository_tree: {e}")
        return {}

def _get_repository_tree_ascii_impl(
    repo_name: str,
    org: Optional[str] = None,
    branch: Optional[str] = None,
    show_file_sizes: bool = True,
    max_depth: int = 10,
    sort_by: str = "name"
) -> str:
    """Implementation function for get_repository_tree_ascii."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        # Convert 0 to None for unlimited depth (to match GitHubExplorer API)
        actual_max_depth = None if max_depth == 0 else max_depth
        
        return explorer.get_repository_tree_ascii(
            repo_name=repo_name,
            org=org,
            branch=branch,
            show_file_sizes=show_file_sizes,
            max_depth=actual_max_depth,
            sort_by=sort_by
        )
        
    except Exception as e:
        logger.error(f"Error in get_repository_tree_ascii: {e}")
        return f"❌ Error generating ASCII tree: {e}"

def _list_directory_impl(
    repo_name: str,
    directory_path: str = "",
    org: Optional[str] = None,
    branch: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Implementation function for list_directory."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.list_directory(
            repo_name=repo_name,
            directory_path=directory_path,
            org=org,
            branch=branch
        )
        
    except Exception as e:
        logger.error(f"Error in list_directory: {e}")
        return []

def _get_file_impl(
    repo_name: str,
    file_path: str,
    org: Optional[str] = None,
    branch: Optional[str] = None,
    decode_content: bool = True
) -> Optional[Dict[str, Any]]:
    """Implementation function for get_file."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        file_info = explorer.get_file(
            repo_name=repo_name,
            file_path=file_path,
            org=org,
            branch=branch,
            decode_content=decode_content
        )
        
        if file_info:
            return _convert_file_info_to_dict(file_info)
        return None
        
    except Exception as e:
        logger.error(f"Error in get_file: {e}")
        return None

def _get_files_as_codeblock_impl(
    repo_name: str,
    file_paths: List[str],
    org: Optional[str] = None,
    branch: Optional[str] = None,
    support_globs: bool = True,
    include_line_numbers: bool = False
) -> str:
    """Implementation function for get_files_as_codeblock."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.get_files_as_codeblock(
            repo_name=repo_name,
            file_paths=file_paths,
            org=org,
            branch=branch,
            support_globs=support_globs,
            include_line_numbers=include_line_numbers
        )
        
    except Exception as e:
        logger.error(f"Error in get_files_as_codeblock: {e}")
        return f"❌ Error creating codeblock: {e}"

def _get_pull_requests_impl(
    repo_name: str,
    org: Optional[str] = None,
    state: str = "open",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for get_pull_requests."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        prs = explorer.get_pull_requests(
            repo_name=repo_name,
            org=org,
            state=state,
            limit=limit
        )
        
        # Convert datetime objects to ISO strings
        for pr in prs:
            for field in ['created_at', 'updated_at', 'closed_at', 'merged_at']:
                if field in pr and pr[field]:
                    if isinstance(pr[field], datetime):
                        pr[field] = pr[field].isoformat()
        
        return prs
        
    except Exception as e:
        logger.error(f"Error in get_pull_requests: {e}")
        return []

def _get_commits_impl(
    repo_name: str,
    org: Optional[str] = None,
    branch: Optional[str] = None,
    limit: int = 50,
    since: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Implementation function for get_commits."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        # Parse since parameter if provided
        since_datetime = None
        if since:
            try:
                since_datetime = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid date format for 'since': {since}")
        
        commits = explorer.get_commits(
            repo_name=repo_name,
            org=org,
            branch=branch,
            limit=limit,
            since=since_datetime
        )
        
        # Convert datetime objects to ISO strings
        for commit in commits:
            if 'author' in commit and 'date' in commit['author']:
                if isinstance(commit['author']['date'], datetime):
                    commit['author']['date'] = commit['author']['date'].isoformat()
            if 'committer' in commit and 'date' in commit['committer']:
                if isinstance(commit['committer']['date'], datetime):
                    commit['committer']['date'] = commit['committer']['date'].isoformat()
        
        return commits
        
    except Exception as e:
        logger.error(f"Error in get_commits: {e}")
        return []

def _get_issues_impl(
    repo_name: str,
    org: Optional[str] = None,
    state: str = "open",
    labels: Optional[List[str]] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for get_issues."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        issues = explorer.get_issues(
            repo_name=repo_name,
            org=org,
            state=state,
            labels=labels,
            limit=limit
        )
        
        # Convert datetime objects to ISO strings
        for issue in issues:
            for field in ['created_at', 'updated_at', 'closed_at']:
                if field in issue and issue[field]:
                    if isinstance(issue[field], datetime):
                        issue[field] = issue[field].isoformat()
        
        return issues
        
    except Exception as e:
        logger.error(f"Error in get_issues: {e}")
        return []

def _get_discussions_impl(
    repo_name: str,
    org: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for get_discussions."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.get_discussions(
            repo_name=repo_name,
            org=org,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in get_discussions: {e}")
        return []

# =============================================================================
# ENHANCED FILE SELECTION FUNCTIONS
# =============================================================================

def _get_repository_files_selective_impl(
    repo_name: str,
    file_patterns: List[str],
    org: Optional[str] = None,
    branch: Optional[str] = None,
    format_as_codeblock: bool = True
) -> str:
    """Implementation function for get_repository_files_selective."""
    try:
        _ensure_initialized()
        file_selector = _get_file_selector_instance()
        
        # Resolve file patterns to actual file paths
        resolved_files = file_selector.resolve_file_patterns(
            patterns=file_patterns,
            repo_name=repo_name,
            org=org,
            branch=branch
        )
        
        if not resolved_files:
            return "No files found matching the specified patterns."
        
        # Parse as file specs (no ranges)
        file_specs = [FileSpec(path=file_path, original_spec=file_path) for file_path in resolved_files]
        
        # Fetch files
        file_results = file_selector.fetch_files_with_specs(
            file_specs=file_specs,
            repo_name=repo_name,
            org=org,
            branch=branch
        )
        
        if format_as_codeblock:
            return file_selector.create_formatted_codeblock(
                files=file_results,
                repo_name=repo_name,
                org=org,
                branch=branch
            )
        else:
            # Return as structured text
            content_lines = []
            repo_full_name = f"{org}/{repo_name}" if org else repo_name
            content_lines.append(f"Files from {repo_full_name}:")
            for file_result in file_results:
                content_lines.append(f"\n{file_result.path}:")
                content_lines.append(file_result.content)
            return "\n".join(content_lines)
        
    except Exception as e:
        logger.error(f"Error in get_repository_files_selective: {e}")
        return f"❌ Error: {e}"

def _get_code_snippets_impl(
    repo_name: str,
    file_specs: List[str],
    org: Optional[str] = None,
    branch: Optional[str] = None,
    format_as_codeblock: bool = True
) -> str:
    """Implementation function for get_code_snippets."""
    try:
        _ensure_initialized()
        file_selector = _get_file_selector_instance()
        
        # Parse file specifications
        parsed_specs = []
        for spec in file_specs:
            try:
                parsed_spec = file_selector.parse_file_spec(spec)
                parsed_specs.append(parsed_spec)
            except Exception as e:
                logger.warning(f"Invalid file spec {spec}: {e}")
                continue
        
        if not parsed_specs:
            return "No valid file specifications provided."
        
        # Fetch files with ranges
        file_results = file_selector.fetch_files_with_specs(
            file_specs=parsed_specs,
            repo_name=repo_name,
            org=org,
            branch=branch
        )
        
        if not file_results:
            return "No files could be fetched."
        
        if format_as_codeblock:
            return file_selector.create_formatted_codeblock(
                files=file_results,
                repo_name=repo_name,
                org=org,
                branch=branch
            )
        else:
            # Return as structured text with range info
            content_lines = []
            repo_full_name = f"{org}/{repo_name}" if org else repo_name
            content_lines.append(f"Code snippets from {repo_full_name}:")
            for file_result in file_results:
                content_lines.append(f"\n{file_result.path} ({file_result.range_info}):")
                content_lines.append(file_result.content)
            return "\n".join(content_lines)
        
    except Exception as e:
        logger.error(f"Error in get_code_snippets: {e}")
        return f"❌ Error: {e}"

def _get_files_bulk_data_impl(
    repo_name: str,
    file_specs: List[str],
    org: Optional[str] = None,
    branch: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Implementation function for get_files_bulk_data."""
    try:
        _ensure_initialized()
        file_selector = _get_file_selector_instance()
        
        # Parse file specifications
        parsed_specs = []
        for spec in file_specs:
            try:
                parsed_spec = file_selector.parse_file_spec(spec)
                parsed_specs.append(parsed_spec)
            except Exception as e:
                logger.warning(f"Invalid file spec {spec}: {e}")
                continue
        
        if not parsed_specs:
            return []
        
        # Fetch files
        file_results = file_selector.fetch_files_with_specs(
            file_specs=parsed_specs,
            repo_name=repo_name,
            org=org,
            branch=branch
        )
        
        # Convert to dictionaries
        return [_convert_file_result_to_dict(file_result) for file_result in file_results]
        
    except Exception as e:
        logger.error(f"Error in get_files_bulk_data: {e}")
        return []

def _resolve_file_patterns_impl(
    repo_name: str,
    file_patterns: List[str],
    org: Optional[str] = None,
    branch: Optional[str] = None
) -> List[str]:
    """Implementation function for resolve_file_patterns."""
    try:
        _ensure_initialized()
        file_selector = _get_file_selector_instance()
        
        return file_selector.resolve_file_patterns(
            patterns=file_patterns,
            repo_name=repo_name,
            org=org,
            branch=branch
        )
        
    except Exception as e:
        logger.error(f"Error in resolve_file_patterns: {e}")
        return []

def _get_auth_info_impl() -> Dict[str, Any]:
    """Implementation function for get_auth_info."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        return explorer.get_auth_info()
    except Exception as e:
        logger.error(f"Error getting auth info: {e}")
        return {"error": str(e), "authenticated": False}

# =============================================================================
# CLONE-BASED IMPLEMENTATION FUNCTIONS
# =============================================================================

def _clone_repository_impl(repo_name: str, 
                          org: Optional[str] = None,
                          branch: Optional[str] = None,
                          depth: Optional[int] = 1,
                          recurse_submodules: bool = False,
                          force_reclone: bool = False) -> Optional[Dict[str, Any]]:
    """Implementation function for clone_repository."""
    try:
        from .repo_cloner import get_repository_cloner
        
        _ensure_initialized()
        explorer = _get_explorer()
        cloner = get_repository_cloner()
        
        # Get authentication token
        auth_token = None
        try:
            auth_info = explorer.get_auth_info()
            # Use the same token logic as the explorer
            auth_token = os.getenv('GITHUB_USER_TOKEN') or os.getenv('GITHUB_TOKEN')
        except:
            pass
        
        clone_info = cloner.clone_repository(
            repo_name=repo_name,
            org=org,
            branch=branch,
            auth_token=auth_token,
            depth=depth,
            recurse_submodules=recurse_submodules,
            force_reclone=force_reclone
        )
        
        if clone_info:
            return {
                'repo_name': clone_info.repo_name,
                'org': clone_info.org,
                'branch': clone_info.branch,
                'clone_path': clone_info.clone_path,
                'clone_time': clone_info.clone_time.isoformat(),
                'full_name': clone_info.full_name,
                'with_submodules': clone_info.with_submodules,
                'success': True
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error cloning repository: {e}")
        return None

def _get_files_from_clone_impl(repo_name: str,
                              file_patterns: List[str],
                              org: Optional[str] = None,
                              branch: Optional[str] = None,
                              recurse_submodules: bool = False,
                              format_as_codeblock: bool = True) -> str:
    """Implementation function for get_files_from_clone."""
    try:
        from .repo_cloner import get_repository_cloner
        
        _ensure_initialized()
        explorer = _get_explorer()
        cloner = get_repository_cloner()
        
        # Check if repository is already cloned
        full_name = f"{org}/{repo_name}" if org else repo_name
        clone_key = f"{full_name}#{branch or 'default'}{'#submodules' if recurse_submodules else ''}"
        
        clone_info = None
        if clone_key in cloner.active_clones:
            clone_info = cloner.active_clones[clone_key]
            if not os.path.exists(clone_info.clone_path):
                clone_info = None
        
        # Clone if not available
        if not clone_info:
            submodule_msg = " with submodules" if recurse_submodules else ""
            print(f"🔄 Repository not cloned yet, cloning {full_name}{submodule_msg}...")
            auth_token = os.getenv('GITHUB_USER_TOKEN') or os.getenv('GITHUB_TOKEN')
            clone_info = cloner.clone_repository(
                repo_name=repo_name,
                org=org,
                branch=branch,
                auth_token=auth_token,
                depth=1,  # Shallow clone for speed
                recurse_submodules=recurse_submodules
            )
            
            if not clone_info:
                # Fallback to API if clone fails
                print("⚠️  Clone failed, falling back to API method...")
                return _get_repository_files_selective_impl(repo_name, file_patterns, org, branch, format_as_codeblock)
        
        # Get files from clone
        file_results = cloner.get_files_from_clone(clone_info, file_patterns, include_content=True)
        
        if not file_results:
            return f"# No files found matching patterns: {file_patterns}\n"
        
        if format_as_codeblock:
            # Format as code blocks
            result_blocks = []
            
            # Header
            submodule_info = " (with submodules)" if clone_info.with_submodules else ""
            summary = f"# 📁 Repository: {clone_info.full_name}{submodule_info} (Local Clone)\n"
            summary += f"# 📊 Files: {len(file_results)} found\n"
            if clone_info.branch:
                summary += f"# 🌿 Branch: {clone_info.branch}\n"
            summary += f"# 📂 Clone Path: {clone_info.clone_path}\n"
            summary += f"# 🕒 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            result_blocks.append(summary)
            
            for file_info in file_results:
                if file_info.get('content') is not None:
                    # Determine file extension for syntax highlighting
                    extension = explorer._get_file_extension_for_highlighting(file_info['name'])
                    
                    # Build the code block
                    block_parts = []
                    block_parts.append(f"{clone_info.full_name}/{file_info['path']}")
                    block_parts.append("")  # Empty line
                    block_parts.append(f"```{extension}")
                    block_parts.append(file_info['content'])
                    block_parts.append("```")
                    block_parts.append("")  # Empty line for separation
                    
                    result_blocks.append('\n'.join(block_parts))
                else:
                    # File couldn't be read
                    if file_info.get('is_binary'):
                        result_blocks.append(f"# 📄 Binary file: {file_info['path']} ({file_info['size']} bytes)\n")
                    else:
                        result_blocks.append(f"# ❌ Could not read: {file_info['path']}\n")
            
            return '\n'.join(result_blocks)
        else:
            # Return structured text
            submodule_info = " (with submodules)" if clone_info.with_submodules else ""
            lines = [f"Repository: {clone_info.full_name}{submodule_info} (Local Clone)"]
            lines.append(f"Files found: {len(file_results)}")
            lines.append("")
            
            for file_info in file_results:
                lines.append(f"File: {file_info['path']}")
                lines.append(f"Size: {file_info['size']} bytes")
                if file_info.get('content'):
                    lines.append("Content:")
                    lines.append(file_info['content'])
                else:
                    lines.append("Content: [Binary or unreadable]")
                lines.append("-" * 50)
            
            return '\n'.join(lines)
            
    except Exception as e:
        logger.error(f"Error getting files from clone: {e}")
        # Fallback to API method
        print(f"⚠️  Clone method failed ({e}), falling back to API...")
        return _get_repository_files_selective_impl(repo_name, file_patterns, org, branch, format_as_codeblock)

def _cleanup_clone_impl(repo_name: str,
                       org: Optional[str] = None,
                       branch: Optional[str] = None) -> bool:
    """Implementation function for cleanup_clone."""
    try:
        from .repo_cloner import get_repository_cloner
        
        cloner = get_repository_cloner()
        full_name = f"{org}/{repo_name}" if org else repo_name
        clone_key = f"{full_name}#{branch or 'default'}"
        
        return cloner.cleanup_clone(clone_key)
        
    except Exception as e:
        logger.error(f"Error cleaning up clone: {e}")
        return False

def _get_clone_status_impl() -> Dict[str, Any]:
    """Implementation function for get_clone_status."""
    try:
        from .repo_cloner import get_repository_cloner
        
        cloner = get_repository_cloner()
        return cloner.get_clone_status()
        
    except Exception as e:
        logger.error(f"Error getting clone status: {e}")
        return {"error": str(e), "active_clones": 0}

def _search_issues_impl(
    query: str,
    repo: Optional[str] = None,
    org: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for search_issues."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.search_issues(
            query=query,
            repo=repo,
            org=org,
            state=state,
            labels=labels,
            sort=sort,
            order=order,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in search_issues: {e}")
        return []

def _search_commits_impl(
    query: str,
    repo: Optional[str] = None,
    org: Optional[str] = None,
    author: Optional[str] = None,
    committer: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for search_commits."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.search_commits(
            query=query,
            repo=repo,
            org=org,
            author=author,
            committer=committer,
            sort=sort,
            order=order,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in search_commits: {e}")
        return []

def _search_repositories_impl(
    query: str,
    org: Optional[str] = None,
    language: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for search_repositories."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.search_repositories(
            query=query,
            org=org,
            language=language,
            sort=sort,
            order=order,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in search_repositories: {e}")
        return []

def _search_users_impl(
    query: str,
    type: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for search_users."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.search_users(
            query=query,
            type=type,
            sort=sort,
            order=order,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in search_users: {e}")
        return []

def _search_topics_impl(
    query: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Implementation function for search_topics."""
    try:
        _ensure_initialized()
        explorer = _get_explorer()
        
        return explorer.search_topics(
            query=query,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in search_topics: {e}")
        return []

def _get_repository_info_from_git_folder_impl(
    git_folder_path: str = ".",
    extract_branch_info: bool = True,
    extract_remote_info: bool = True,
    extract_commit_history: bool = False,
    extract_repository_stats: bool = False,
    extract_recent_activity: bool = False,
    commit_history_limit: int = 50
) -> Optional[Dict[str, Any]]:
    """
    Implementation function for extracting GitHub repository information from a local .git folder.
    
    Args:
        git_folder_path: Path to directory containing .git folder
        extract_branch_info: Whether to include current branch and branch list
        extract_remote_info: Whether to include all remote information
        extract_commit_history: Whether to include detailed commit history
        extract_repository_stats: Whether to include repository statistics
        extract_recent_activity: Whether to include recent activity analysis
        commit_history_limit: Maximum number of commits to include in history
        
    Returns:
        Dict with repository information or None if not a git repo or not GitHub
    """
    try:
        # Convert to Path object for easier handling
        base_path = Path(git_folder_path).resolve()
        
        # Find .git directory (could be file in case of worktrees/submodules)
        git_path = base_path / ".git"
        if not git_path.exists():
            # Try parent directories
            for parent in base_path.parents:
                git_path = parent / ".git"
                if git_path.exists():
                    base_path = parent
                    break
            else:
                return None
        
        # Handle .git file (worktree/submodule case)
        if git_path.is_file():
            with open(git_path, 'r') as f:
                git_dir_line = f.read().strip()
                if git_dir_line.startswith('gitdir: '):
                    git_dir = git_dir_line[8:]
                    if not Path(git_dir).is_absolute():
                        git_dir = base_path / git_dir
                    git_path = Path(git_dir)
        
        if not git_path.is_dir():
            return None
            
        # Parse .git/config
        config_path = git_path / "config"
        if not config_path.exists():
            return None
            
        config = configparser.ConfigParser()
        try:
            config.read(config_path)
        except Exception as e:
            logger.warning(f"Could not parse git config: {e}")
            return None
        
        # Extract GitHub remotes
        github_remotes = {}
        primary_remote = None
        
        for section_name in config.sections():
            if section_name.startswith('remote "'):
                remote_name = section_name[8:-1]  # Remove 'remote "' and '"'
                if 'url' in config[section_name]:
                    url = config[section_name]['url']
                    
                    # Check if it's a GitHub URL
                    github_info = _parse_github_url(url)
                    if github_info:
                        github_remotes[remote_name] = {
                            'url': url,
                            'org': github_info['org'],
                            'repo': github_info['repo'],
                            'github_url': github_info['github_url'],
                            'clone_url': github_info['clone_url']
                        }
                        
                        # Prefer 'origin' as primary, otherwise use first found
                        if remote_name == 'origin' or primary_remote is None:
                            primary_remote = remote_name
        
        if not github_remotes:
            return None  # No GitHub remotes found
            
        primary_info = github_remotes[primary_remote]
        
        result = {
            'repo_name': primary_info['repo'],
            'org': primary_info['org'],
            'github_url': primary_info['github_url'],
            'clone_url': primary_info['clone_url'],
            'primary_remote': primary_remote,
            'can_use_github_api': True,
            'local_path': str(base_path),
            'git_path': str(git_path)
        }
        
        # Add all remotes if requested
        if extract_remote_info:
            result['remotes'] = github_remotes
        
        # Extract branch information
        if extract_branch_info:
            try:
                # Get current branch
                current_branch = _get_current_branch(base_path)
                if current_branch:
                    result['current_branch'] = current_branch
                
                # Get default branch from primary remote
                default_branch = _get_default_branch_from_remote(base_path, primary_remote)
                if default_branch:
                    result['default_branch'] = default_branch
                
                # Get list of all branches
                branches = _get_all_branches(base_path)
                if branches:
                    result['branches'] = branches
                    
            except Exception as e:
                logger.warning(f"Could not extract branch info: {e}")
        
        # Add repository status information
        try:
            status_info = _get_repository_status(base_path)
            result.update(status_info)
        except Exception as e:
            logger.warning(f"Could not get repository status: {e}")
        
        # Extract detailed commit history
        if extract_commit_history:
            try:
                commit_history = _get_detailed_commit_history(base_path, commit_history_limit)
                if commit_history:
                    result['commit_history'] = commit_history
            except Exception as e:
                logger.warning(f"Could not extract commit history: {e}")
        
        # Extract repository statistics
        if extract_repository_stats:
            try:
                repo_stats = _get_repository_statistics(base_path)
                result['repository_stats'] = repo_stats
            except Exception as e:
                logger.warning(f"Could not extract repository stats: {e}")
        
        # Extract recent activity
        if extract_recent_activity:
            try:
                recent_activity = _get_recent_activity(base_path)
                result['recent_activity'] = recent_activity
            except Exception as e:
                logger.warning(f"Could not extract recent activity: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting git repository info: {e}")
        return None

def _parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """Parse a GitHub URL to extract org and repo name."""
    # GitHub URL patterns
    patterns = [
        r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
        r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$',
        r'ssh://git@github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url.strip())
        if match:
            org, repo = match.groups()
            repo = repo.rstrip('.git')  # Remove .git suffix if present
            return {
                'org': org,
                'repo': repo,
                'github_url': f'https://github.com/{org}/{repo}',
                'clone_url': f'https://github.com/{org}/{repo}.git'
            }
    
    return None

def _get_current_branch(repo_path: Path) -> Optional[str]:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            return branch if branch else None
    except Exception:
        pass
    
    # Fallback: parse HEAD file
    try:
        head_path = repo_path / '.git' / 'HEAD'
        if head_path.exists():
            with open(head_path, 'r') as f:
                head_content = f.read().strip()
                if head_content.startswith('ref: refs/heads/'):
                    return head_content[16:]  # Remove 'ref: refs/heads/'
    except Exception:
        pass
    
    return None

def _get_default_branch_from_remote(repo_path: Path, remote_name: str) -> Optional[str]:
    """Get the default branch from the remote."""
    try:
        result = subprocess.run(
            ['git', 'symbolic-ref', f'refs/remotes/{remote_name}/HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            ref = result.stdout.strip()
            if ref.startswith(f'refs/remotes/{remote_name}/'):
                return ref[len(f'refs/remotes/{remote_name}/'):]
    except Exception:
        pass
    
    # Fallback to common default branch names
    for branch in ['main', 'master', 'develop']:
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', f'refs/remotes/{remote_name}/{branch}'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return branch
        except Exception:
            continue
    
    return None

def _get_all_branches(repo_path: Path) -> Optional[Dict[str, List[str]]]:
    """Get all local and remote branches."""
    try:
        branches = {'local': [], 'remote': []}
        
        # Get local branches
        result = subprocess.run(
            ['git', 'branch'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                branch = line.strip().lstrip('* ')
                if branch and not branch.startswith('('):
                    branches['local'].append(branch)
        
        # Get remote branches
        result = subprocess.run(
            ['git', 'branch', '-r'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                branch = line.strip()
                if branch and '->' not in branch and not branch.startswith('('):
                    branches['remote'].append(branch)
        
        return branches if branches['local'] or branches['remote'] else None
        
    except Exception:
        return None

def _get_repository_status(repo_path: Path) -> Dict[str, Any]:
    """Get repository status information."""
    status = {}
    
    try:
        # Check if there are uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            status['has_uncommitted_changes'] = bool(result.stdout.strip())
            status['uncommitted_files_count'] = len(result.stdout.splitlines()) if result.stdout.strip() else 0
    except Exception:
        pass
    
    try:
        # Get last commit info
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H|%an|%ae|%s|%ci'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split('|', 4)
            if len(parts) == 5:
                status['last_commit'] = {
                    'hash': parts[0],
                    'author_name': parts[1],
                    'author_email': parts[2],
                    'message': parts[3],
                    'date': parts[4]
                }
    except Exception:
        pass
    
    return status

def _get_detailed_commit_history(repo_path: Path, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
    """Get detailed commit history with file changes."""
    try:
        # Get commit log with detailed information
        result = subprocess.run(
            ['git', 'log', f'-{limit}', '--format=%H|%an|%ae|%s|%ci|%P', '--stat', '--numstat'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        commits = []
        current_commit = None
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a commit header line
            if '|' in line and len(line.split('|')) == 6:
                # Save previous commit if exists
                if current_commit:
                    commits.append(current_commit)
                
                # Parse new commit
                parts = line.split('|', 5)
                current_commit = {
                    'hash': parts[0],
                    'author_name': parts[1],
                    'author_email': parts[2],
                    'message': parts[3],
                    'date': parts[4],
                    'parents': parts[5].split() if parts[5] else [],
                    'files_changed': [],
                    'stats': {'insertions': 0, 'deletions': 0, 'files': 0}
                }
            elif current_commit and '\t' in line:
                # This is file change info (numstat format: insertions\tdeletions\tfilename)
                parts = line.split('\t', 2)
                if len(parts) == 3:
                    try:
                        insertions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                        filename = parts[2]
                        
                        current_commit['files_changed'].append({
                            'filename': filename,
                            'insertions': insertions,
                            'deletions': deletions
                        })
                        
                        current_commit['stats']['insertions'] += insertions
                        current_commit['stats']['deletions'] += deletions
                        current_commit['stats']['files'] += 1
                    except ValueError:
                        continue
        
        # Add the last commit
        if current_commit:
            commits.append(current_commit)
        
        return commits
        
    except Exception:
        return None

def _get_repository_statistics(repo_path: Path) -> Dict[str, Any]:
    """Get comprehensive repository statistics."""
    stats = {}
    
    try:
        # Total commit count
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            stats['total_commits'] = int(result.stdout.strip())
    except Exception:
        pass
    
    try:
        # Contributors with commit counts
        result = subprocess.run(
            ['git', 'shortlog', '-sn', '--all'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            contributors = []
            for line in result.stdout.splitlines():
                if line.strip():
                    parts = line.strip().split('\t', 1)
                    if len(parts) == 2:
                        contributors.append({
                            'name': parts[1],
                            'commits': int(parts[0])
                        })
            stats['contributors'] = contributors
            stats['total_contributors'] = len(contributors)
    except Exception:
        pass
    
    try:
        # Repository age (first commit date)
        result = subprocess.run(
            ['git', 'log', '--reverse', '--format=%ci', '-1'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            stats['first_commit_date'] = result.stdout.strip()
    except Exception:
        pass
    
    try:
        # File statistics
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            files = result.stdout.splitlines()
            stats['total_files'] = len(files)
            
            # File type distribution
            file_types = {}
            for file in files:
                ext = Path(file).suffix.lower()
                if not ext:
                    ext = 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            
            stats['file_types'] = dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True))
    except Exception:
        pass
    
    try:
        # Repository size (objects)
        objects_path = repo_path / '.git' / 'objects'
        if objects_path.exists():
            object_count = 0
            total_size = 0
            for root, dirs, files in os.walk(objects_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        total_size += size
                        object_count += 1
                    except:
                        continue
            
            stats['git_objects'] = {
                'count': object_count,
                'size_mb': round(total_size / (1024 * 1024), 2)
            }
    except Exception:
        pass
    
    return stats

def _get_recent_activity(repo_path: Path, days: int = 30) -> Dict[str, Any]:
    """Get recent activity analysis."""
    activity = {}
    
    try:
        # Recent commits (last 30 days)
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = subprocess.run(
            ['git', 'log', f'--since={since_date}', '--format=%H|%an|%ci|%s'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            recent_commits = []
            for line in result.stdout.splitlines():
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        recent_commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            activity['recent_commits'] = recent_commits
            activity['commits_last_30_days'] = len(recent_commits)
    except Exception:
        pass
    
    try:
        # Most frequently changed files (last 100 commits)
        result = subprocess.run(
            ['git', 'log', '-100', '--name-only', '--format='],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            file_changes = {}
            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith('commit'):
                    file_changes[line.strip()] = file_changes.get(line.strip(), 0) + 1
            
            # Sort by frequency and take top 10
            frequent_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:10]
            activity['most_changed_files'] = [
                {'filename': f[0], 'changes': f[1]} for f in frequent_files
            ]
    except Exception:
        pass
    
    try:
        # Active contributors (last 30 days)
        result = subprocess.run(
            ['git', 'shortlog', '-sn', f'--since={since_date}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            active_contributors = []
            for line in result.stdout.splitlines():
                if line.strip():
                    parts = line.strip().split('\t', 1)
                    if len(parts) == 2:
                        active_contributors.append({
                            'name': parts[1],
                            'commits': int(parts[0])
                        })
            activity['active_contributors'] = active_contributors
    except Exception:
        pass
    
    return activity

def _get_file_at_commit_impl(
    git_folder_path: str,
    file_path: str,
    commit_hash: str
) -> Optional[Dict[str, Any]]:
    """Get file content at a specific commit."""
    try:
        base_path = Path(git_folder_path).resolve()
        
        # Verify this is a git repository
        if not (base_path / ".git").exists():
            return None
        
        # Get file content at specific commit
        result = subprocess.run(
            ['git', 'show', f'{commit_hash}:{file_path}'],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode != 0:
            return None
        
        # Get commit info for context
        commit_result = subprocess.run(
            ['git', 'show', '--format=%H|%an|%ae|%s|%ci', '--no-patch', commit_hash],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        commit_info = {}
        if commit_result.returncode == 0:
            parts = commit_result.stdout.strip().split('|', 4)
            if len(parts) == 5:
                commit_info = {
                    'hash': parts[0],
                    'author_name': parts[1],
                    'author_email': parts[2],
                    'message': parts[3],
                    'date': parts[4]
                }
        
        return {
            'file_path': file_path,
            'commit_hash': commit_hash,
            'content': result.stdout,
            'commit_info': commit_info,
            'repository_path': str(base_path)
        }
        
    except Exception as e:
        logger.error(f"Error getting file at commit: {e}")
        return None

def _get_file_history_impl(
    git_folder_path: str,
    file_path: str,
    limit: int = 50,
    include_patches: bool = False
) -> Optional[Dict[str, Any]]:
    """Get comprehensive history of changes to a specific file."""
    try:
        base_path = Path(git_folder_path).resolve()
        
        if not (base_path / ".git").exists():
            return None
        
        # Build git log command
        cmd = ['git', 'log', f'-{limit}', '--follow']
        if include_patches:
            cmd.append('-p')
        cmd.extend(['--format=%H|%an|%ae|%s|%ci', '--', file_path])
        
        result = subprocess.run(
            cmd,
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        commits = []
        current_commit = None
        current_patch = []
        
        for line in result.stdout.splitlines():
            # Check if this is a commit header
            if '|' in line and len(line.split('|')) == 5:
                # Save previous commit
                if current_commit:
                    if include_patches and current_patch:
                        current_commit['patch'] = '\n'.join(current_patch)
                    commits.append(current_commit)
                
                # Parse new commit
                parts = line.split('|', 4)
                current_commit = {
                    'hash': parts[0],
                    'author_name': parts[1],
                    'author_email': parts[2],
                    'message': parts[3],
                    'date': parts[4]
                }
                current_patch = []
            elif include_patches and current_commit:
                current_patch.append(line)
        
        # Add the last commit
        if current_commit:
            if include_patches and current_patch:
                current_commit['patch'] = '\n'.join(current_patch)
            commits.append(current_commit)
        
        return {
            'file_path': file_path,
            'repository_path': str(base_path),
            'total_commits': len(commits),
            'commits': commits
        }
        
    except Exception as e:
        logger.error(f"Error getting file history: {e}")
        return None

def _get_file_blame_impl(
    git_folder_path: str,
    file_path: str,
    commit_hash: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get git blame information showing who changed each line."""
    try:
        base_path = Path(git_folder_path).resolve()
        
        if not (base_path / ".git").exists():
            return None
        
        # Build git blame command
        cmd = ['git', 'blame', '--line-porcelain']
        if commit_hash:
            cmd.append(commit_hash)
        cmd.append(file_path)
        
        result = subprocess.run(
            cmd,
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=20
        )
        
        if result.returncode != 0:
            return None
        
        # Parse blame output
        blame_lines = []
        current_commit = None
        commit_cache = {}
        
        for line in result.stdout.splitlines():
            if line.startswith('\t'):
                # This is the actual file content line
                if current_commit:
                    blame_lines.append({
                        'line_number': len(blame_lines) + 1,
                        'content': line[1:],  # Remove tab
                        'commit_hash': current_commit['hash'],
                        'author': current_commit['author'],
                        'date': current_commit['date'],
                        'summary': current_commit.get('summary', '')
                    })
            elif ' ' in line:
                # This is commit metadata
                parts = line.split(' ', 1)
                commit_hash_line = parts[0]
                
                if commit_hash_line not in commit_cache:
                    commit_cache[commit_hash_line] = {'hash': commit_hash_line}
                
                current_commit = commit_cache[commit_hash_line]
            elif line.startswith('author '):
                if current_commit:
                    current_commit['author'] = line[7:]
            elif line.startswith('author-time '):
                if current_commit:
                    timestamp = int(line[12:])
                    current_commit['date'] = datetime.fromtimestamp(timestamp).isoformat()
            elif line.startswith('summary '):
                if current_commit:
                    current_commit['summary'] = line[8:]
        
        return {
            'file_path': file_path,
            'repository_path': str(base_path),
            'commit_hash': commit_hash,
            'total_lines': len(blame_lines),
            'blame_lines': blame_lines
        }
        
    except Exception as e:
        logger.error(f"Error getting file blame: {e}")
        return None

def _search_file_changes_impl(
    git_folder_path: str,
    file_path: str,
    search_term: str,
    context_lines: int = 3
) -> Optional[Dict[str, Any]]:
    """Search for when specific code/text was added or removed from a file."""
    try:
        base_path = Path(git_folder_path).resolve()
        
        if not (base_path / ".git").exists():
            return None
        
        # Search for additions and deletions of the term
        result = subprocess.run(
            ['git', 'log', '-p', '-S', search_term, '--', file_path],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return None
        
        # Also search in commit messages
        message_result = subprocess.run(
            ['git', 'log', '--grep', search_term, '--format=%H|%an|%ae|%s|%ci', '--', file_path],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        commits_with_term = []
        commits_in_messages = []
        
        # Parse commits that modified the search term
        current_commit = None
        current_changes = []
        
        for line in result.stdout.splitlines():
            if line.startswith('commit '):
                if current_commit and current_changes:
                    current_commit['changes'] = '\n'.join(current_changes)
                    commits_with_term.append(current_commit)
                
                commit_hash = line.split()[1]
                current_commit = {'hash': commit_hash}
                current_changes = []
            elif line.startswith('Author: '):
                if current_commit:
                    current_commit['author'] = line[8:]
            elif line.startswith('Date: '):
                if current_commit:
                    current_commit['date'] = line[6:].strip()
            elif line.startswith('    ') and current_commit and 'message' not in current_commit:
                current_commit['message'] = line.strip()
            elif (line.startswith('+') or line.startswith('-')) and search_term in line:
                current_changes.append(line)
        
        # Add the last commit
        if current_commit and current_changes:
            current_commit['changes'] = '\n'.join(current_changes)
            commits_with_term.append(current_commit)
        
        # Parse commits with term in message
        if message_result.returncode == 0:
            for line in message_result.stdout.splitlines():
                if line.strip():
                    parts = line.split('|', 4)
                    if len(parts) == 5:
                        commits_in_messages.append({
                            'hash': parts[0],
                            'author_name': parts[1],
                            'author_email': parts[2],
                            'message': parts[3],
                            'date': parts[4]
                        })
        
        return {
            'file_path': file_path,
            'search_term': search_term,
            'repository_path': str(base_path),
            'commits_with_code_changes': commits_with_term,
            'commits_with_message_mentions': commits_in_messages,
            'total_matches': len(commits_with_term) + len(commits_in_messages)
        }
        
    except Exception as e:
        logger.error(f"Error searching file changes: {e}")
        return None

def _compare_file_versions_impl(
    git_folder_path: str,
    file_path: str,
    commit1: str,
    commit2: str = "HEAD"
) -> Optional[Dict[str, Any]]:
    """Compare two versions of a file between commits."""
    try:
        base_path = Path(git_folder_path).resolve()
        
        if not (base_path / ".git").exists():
            return None
        
        # Get diff between the two commits for this file
        result = subprocess.run(
            ['git', 'diff', commit1, commit2, '--', file_path],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=20
        )
        
        if result.returncode != 0:
            return None
        
        # Get commit info for both commits
        def get_commit_info(commit):
            info_result = subprocess.run(
                ['git', 'show', '--format=%H|%an|%ae|%s|%ci', '--no-patch', commit],
                cwd=base_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if info_result.returncode == 0:
                parts = info_result.stdout.strip().split('|', 4)
                if len(parts) == 5:
                    return {
                        'hash': parts[0],
                        'author_name': parts[1],
                        'author_email': parts[2],
                        'message': parts[3],
                        'date': parts[4]
                    }
            return {'hash': commit}
        
        commit1_info = get_commit_info(commit1)
        commit2_info = get_commit_info(commit2)
        
        # Parse diff statistics
        stat_result = subprocess.run(
            ['git', 'diff', '--stat', commit1, commit2, '--', file_path],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        stats = {}
        if stat_result.returncode == 0 and stat_result.stdout.strip():
            # Parse stats like "file.py | 10 +++++-----"
            stat_line = stat_result.stdout.strip().split('\n')[-1]
            if '|' in stat_line:
                parts = stat_line.split('|')[1].strip().split()
                if parts:
                    changes = parts[0]
                    try:
                        stats['total_changes'] = int(changes)
                    except ValueError:
                        pass
        
        return {
            'file_path': file_path,
            'repository_path': str(base_path),
            'commit1': commit1_info,
            'commit2': commit2_info,
            'diff': result.stdout,
            'stats': stats,
            'has_changes': bool(result.stdout.strip())
        }
        
    except Exception as e:
        logger.error(f"Error comparing file versions: {e}")
        return None 