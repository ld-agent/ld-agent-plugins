# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "GitHub Browser",
    "description": "Browse and explore GitHub repositories with AI-focused tools and enhanced file selection capabilities",
    "author": "arcana team",
    "version": "2.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": ["PyGithub>=1.59.0", "pydantic>=2.0.0", "urllib3"],
    "environment_variables": {
        "GITHUB_TOKEN": {
            "description": "GitHub personal access token or app token for API access",
            "default": "",
            "required": False
        },
        "GITHUB_USER_TOKEN": {
            "description": "GitHub personal access token for user-level operations (accessing personal repos)",
            "default": "",
            "required": False
        },
        "GITHUB_AUTH_PREFERENCE": {
            "description": "Authentication preference: 'app' (GitHub App), 'user' (personal token), or 'auto' (intelligent fallback)",
            "default": "auto",
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
        },
        "GITHUB_APP_ID": {
            "description": "GitHub App ID for app authentication",
            "default": "",
            "required": False
        },
        "GITHUB_PRIVATE_KEY_PATH": {
            "description": "Path to GitHub App private key file",
            "default": "",
            "required": False
        },
        "GITHUB_CLONE_ENABLED": {
            "description": "Enable local repository cloning for bulk operations",
            "default": "true",
            "required": False
        },
        "GITHUB_CLONE_MAX_SIZE_MB": {
            "description": "Maximum repository size to clone in MB (safety limit)",
            "default": "500",
            "required": False
        },
        "GITHUB_CLONE_AUTO_CLEANUP_HOURS": {
            "description": "Hours after which to auto-cleanup old clones",
            "default": "24",
            "required": False
        }
    }
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

from typing import Annotated, Optional, Dict, Any, List
from pydantic import Field
from datetime import datetime

# Import implementation functions
from .github_functions import (
    _initialize_plugin_impl,
    _search_files_impl,
    _search_content_impl,
    _list_repositories_impl,
    _get_repository_info_impl,
    _get_contributors_impl,
    _get_repository_tree_impl,
    _get_repository_tree_ascii_impl,
    _list_directory_impl,
    _get_file_impl,
    _get_files_as_codeblock_impl,
    _get_pull_requests_impl,
    _get_commits_impl,
    _get_issues_impl,
    _get_discussions_impl,
    # Enhanced file selection functions
    _get_repository_files_selective_impl,
    _get_code_snippets_impl,
    _get_files_bulk_data_impl,
    _resolve_file_patterns_impl,
    _get_auth_info_impl,
    # Clone-based functions
    _clone_repository_impl,
    _get_files_from_clone_impl,
    _cleanup_clone_impl,
    _get_clone_status_impl,
    _search_issues_impl,
    _search_commits_impl,
    _search_repositories_impl,
    _search_users_impl,
    _search_topics_impl,
    # Local git functions
    _get_repository_info_from_git_folder_impl,
    # File history and forensic functions
    _get_file_at_commit_impl,
    _get_file_history_impl,
    _get_file_blame_impl,
    _search_file_changes_impl,
    _compare_file_versions_impl
)

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

def initialize_plugin() -> None:
    """
    Initialize the GitHub Browser plugin with current environment variables.
    This should be called by agentkit after environment setup.
    """
    return _initialize_plugin_impl()

def get_auth_info() -> Dict[str, Any]:
    """
    Get information about current authentication method and capabilities.
    
    Returns:
        Dict[str, Any]: Authentication info including method, user, and capabilities
    """
    return _get_auth_info_impl()

def get_repository_info_from_git_folder(
    git_folder_path: Annotated[str, Field(description="Path to directory containing .git folder (defaults to current directory)", default=".")] = ".",
    extract_branch_info: Annotated[bool, Field(description="Whether to include current branch and branch list", default=True)] = True,
    extract_remote_info: Annotated[bool, Field(description="Whether to include all remote information", default=True)] = True,
    extract_commit_history: Annotated[bool, Field(description="Whether to include detailed commit history with file changes", default=False)] = False,
    extract_repository_stats: Annotated[bool, Field(description="Whether to include comprehensive repository statistics", default=False)] = False,
    extract_recent_activity: Annotated[bool, Field(description="Whether to include recent activity analysis (last 30 days)", default=False)] = False,
    commit_history_limit: Annotated[int, Field(description="Maximum number of commits to include in history", ge=1, le=1000, default=50)] = 50
) -> Optional[Dict[str, Any]]:
    """
    Extract GitHub repository information from a local .git folder.
    
    This function parses the .git/config file and git metadata to determine
    the GitHub repository URL, organization, repository name, current branch,
    and other useful information for further GitHub API operations.
    
    🚀 **NEW: Deep Repository Analysis!**
    Now extracts comprehensive local git data including commit history,
    contributor statistics, file change patterns, and recent activity.
    Perfect for code review automation and repository insights!
    
    Args:
        git_folder_path: Path to directory containing .git folder (defaults to current directory)
        extract_branch_info: Whether to include current branch and branch list
        extract_remote_info: Whether to include all remote information
        extract_commit_history: Whether to include detailed commit history with file changes
        extract_repository_stats: Whether to include comprehensive repository statistics
        extract_recent_activity: Whether to include recent activity analysis (last 30 days)
        commit_history_limit: Maximum number of commits to include in history
        
    Returns:
        Dict with repository information including:
        
        **Basic Info (always included):**
        - repo_name: Repository name
        - org: Organization/owner name  
        - github_url: Full GitHub repository URL
        - clone_url: Clone URL for this repo
        - can_use_github_api: Boolean indicating if this can be used with other plugin functions
        - local_path: Absolute path to the local repository
        - has_uncommitted_changes: Whether there are uncommitted changes
        - last_commit: Information about the last commit
        
        **Branch Info (if extract_branch_info=True):**
        - current_branch: Current branch name
        - default_branch: Default branch name
        - branches: Dict with 'local' and 'remote' branch lists
        
        **Remote Info (if extract_remote_info=True):**
        - remotes: Dict of all configured remotes
        
        **Commit History (if extract_commit_history=True):**
        - commit_history: Detailed list of commits with file changes, stats, and metadata
        
        **Repository Stats (if extract_repository_stats=True):**
        - repository_stats: Comprehensive statistics including:
          - total_commits: Total number of commits
          - contributors: List of contributors with commit counts
          - total_contributors: Number of unique contributors
          - first_commit_date: Date of first commit
          - total_files: Number of tracked files
          - file_types: Distribution of file types
          - git_objects: Repository size and object count
        
        **Recent Activity (if extract_recent_activity=True):**
        - recent_activity: Activity analysis including:
          - recent_commits: Commits from last 30 days
          - commits_last_30_days: Count of recent commits
          - most_changed_files: Files that change most frequently
          - active_contributors: Recent contributors
        
        Returns None if not a git repository or no GitHub remotes found.
        
    Examples:
        >>> # Basic usage (fast)
        >>> repo_info = get_repository_info_from_git_folder()
        >>> print(f"Working on: {repo_info['org']}/{repo_info['repo_name']}")
        
        >>> # Deep analysis (comprehensive)
        >>> repo_info = get_repository_info_from_git_folder(
        ...     extract_commit_history=True,
        ...     extract_repository_stats=True,
        ...     extract_recent_activity=True,
        ...     commit_history_limit=100
        ... )
        >>> 
        >>> # Now you have rich repository insights:
        >>> print(f"Total commits: {repo_info['repository_stats']['total_commits']}")
        >>> print(f"Contributors: {repo_info['repository_stats']['total_contributors']}")
        >>> print(f"Recent activity: {repo_info['recent_activity']['commits_last_30_days']} commits")
        >>> 
        >>> # Use with other github_browser functions
        >>> commits = get_commits(repo_info['repo_name'], repo_info['org'])
        >>> issues = get_issues(repo_info['repo_name'], repo_info['org'])
    """
    return _get_repository_info_from_git_folder_impl(
        git_folder_path=git_folder_path,
        extract_branch_info=extract_branch_info,
        extract_remote_info=extract_remote_info,
        extract_commit_history=extract_commit_history,
        extract_repository_stats=extract_repository_stats,
        extract_recent_activity=extract_recent_activity,
        commit_history_limit=commit_history_limit
    )

# =============================================================================
# ORIGINAL GITHUB BROWSER TOOLS
# =============================================================================

def search_files(
    query: Annotated[str, Field(description="Search query (filename or partial filename)")],
    repo: Annotated[Optional[str], Field(description="Specific repository name (if None, searches across org)", default=None)] = None,
    org: Annotated[Optional[str], Field(description="Organization name (defaults to GITHUB_ORG env var)", default=None)] = None,
    path: Annotated[Optional[str], Field(description="Limit search to specific path", default=None)] = None,
    extension: Annotated[Optional[str], Field(description="File extension filter (e.g., 'py', 'js')", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum results to return", ge=1, le=1000, default=100)] = 100
) -> List[Dict[str, Any]]:
    """
    Search for files using GitHub's search API.
    
    This function searches for files by name across repositories or within
    a specific repository. It returns file metadata including paths, sizes,
    and URLs.
    
    Args:
        query: Search query (filename or partial filename)
        repo: Specific repository name (if None, searches across org)
        org: Organization name (defaults to GITHUB_ORG env var)
        path: Limit search to specific path
        extension: File extension filter (e.g., 'py', 'js')
        limit: Maximum results to return
        
    Returns:
        List[Dict[str, Any]]: List of file information objects
        
    Example:
        >>> files = search_files("config", repo="myrepo", extension="json")
        >>> print(files[0]['name'])
        "config.json"
    """
    return _search_files_impl(query=query, repo=repo, org=org, path=path, extension=extension, limit=limit)

def search_content(
    query: Annotated[str, Field(description="Content to search for within files")],
    repo: Annotated[Optional[str], Field(description="Specific repository name", default=None)] = None,
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    path: Annotated[Optional[str], Field(description="Limit search to specific path", default=None)] = None,
    extension: Annotated[Optional[str], Field(description="File extension filter", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum results to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Search for content within files using GitHub's search API.
    
    This function searches for specific text content within files and returns
    matches with context information including file paths and repository details.
    
    Args:
        query: Content to search for within files
        repo: Specific repository name
        org: Organization name
        path: Limit search to specific path
        extension: File extension filter
        limit: Maximum results to return
        
    Returns:
        List[Dict[str, Any]]: List of search results with content matches
    """
    return _search_content_impl(query=query, repo=repo, org=org, path=path, extension=extension, limit=limit)

def search_issues(
    query: Annotated[str, Field(description="Search query for issues and pull requests")],
    repo: Annotated[Optional[str], Field(description="Specific repository name", default=None)] = None,
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    state: Annotated[Optional[str], Field(description="Issue state: 'open', 'closed'", default=None)] = None,
    labels: Annotated[Optional[List[str]], Field(description="List of label names to filter by", default=None)] = None,
    sort: Annotated[Optional[str], Field(description="Sort order: 'comments', 'created', 'updated'", default=None)] = None,
    order: Annotated[Optional[str], Field(description="Order: 'asc', 'desc'", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum results to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Search for issues and pull requests using GitHub's search API.
    
    This function searches across issues and pull requests, returning detailed
    information including state, labels, assignees, and repository context.
    
    Args:
        query: Search query for issues and pull requests
        repo: Specific repository name
        org: Organization name
        state: Issue state ('open', 'closed')
        labels: List of label names to filter by
        sort: Sort order ('comments', 'created', 'updated')
        order: Order ('asc', 'desc')
        limit: Maximum results to return
        
    Returns:
        List[Dict[str, Any]]: List of issue/PR search results
        
    Example:
        >>> issues = search_issues("bug", repo="myrepo", state="open", labels=["bug"])
        >>> print(f"Found {len(issues)} open bug reports")
    """
    return _search_issues_impl(query=query, repo=repo, org=org, state=state, labels=labels, sort=sort, order=order, limit=limit)

def search_commits(
    query: Annotated[str, Field(description="Search query for commits")],
    repo: Annotated[Optional[str], Field(description="Specific repository name", default=None)] = None,
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    author: Annotated[Optional[str], Field(description="Commit author", default=None)] = None,
    committer: Annotated[Optional[str], Field(description="Commit committer", default=None)] = None,
    sort: Annotated[Optional[str], Field(description="Sort order: 'author-date', 'committer-date'", default=None)] = None,
    order: Annotated[Optional[str], Field(description="Order: 'asc', 'desc'", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum results to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Search for commits using GitHub's search API.
    
    This function searches commit messages and metadata, returning detailed
    commit information including author, committer, and repository context.
    
    Args:
        query: Search query for commits
        repo: Specific repository name
        org: Organization name
        author: Commit author
        committer: Commit committer
        sort: Sort order ('author-date', 'committer-date')
        order: Order ('asc', 'desc')
        limit: Maximum results to return
        
    Returns:
        List[Dict[str, Any]]: List of commit search results
        
    Example:
        >>> commits = search_commits("fix bug", repo="myrepo", author="username")
        >>> print(f"Found {len(commits)} bug fix commits by user")
    """
    return _search_commits_impl(query=query, repo=repo, org=org, author=author, committer=committer, sort=sort, order=order, limit=limit)

def search_repositories(
    query: Annotated[str, Field(description="Search query for repositories")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    language: Annotated[Optional[str], Field(description="Programming language filter", default=None)] = None,
    sort: Annotated[Optional[str], Field(description="Sort order: 'stars', 'forks', 'updated'", default=None)] = None,
    order: Annotated[Optional[str], Field(description="Order: 'asc', 'desc'", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum results to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Search for repositories using GitHub's search API.
    
    This function searches repository names, descriptions, and topics, returning
    detailed repository information including stars, forks, and language data.
    
    Args:
        query: Search query for repositories
        org: Organization name
        language: Programming language filter
        sort: Sort order ('stars', 'forks', 'updated')
        order: Order ('asc', 'desc')
        limit: Maximum results to return
        
    Returns:
        List[Dict[str, Any]]: List of repository search results
        
    Example:
        >>> repos = search_repositories("machine learning", language="python", sort="stars")
        >>> print(f"Found {len(repos)} popular ML Python repositories")
    """
    return _search_repositories_impl(query=query, org=org, language=language, sort=sort, order=order, limit=limit)

def search_users(
    query: Annotated[str, Field(description="Search query for users")],
    type: Annotated[Optional[str], Field(description="User type: 'user', 'org'", default=None)] = None,
    sort: Annotated[Optional[str], Field(description="Sort order: 'followers', 'repositories', 'joined'", default=None)] = None,
    order: Annotated[Optional[str], Field(description="Order: 'asc', 'desc'", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum results to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Search for users and organizations using GitHub's search API.
    
    This function searches user profiles, returning detailed user information
    including followers, repositories, and profile data.
    
    Args:
        query: Search query for users
        type: User type ('user', 'org')
        sort: Sort order ('followers', 'repositories', 'joined')
        order: Order ('asc', 'desc')
        limit: Maximum results to return
        
    Returns:
        List[Dict[str, Any]]: List of user search results
        
    Example:
        >>> users = search_users("machine learning", type="user", sort="followers")
        >>> print(f"Found {len(users)} ML users sorted by followers")
    """
    return _search_users_impl(query=query, type=type, sort=sort, order=order, limit=limit)

def search_topics(
    query: Annotated[str, Field(description="Search query for topics")],
    limit: Annotated[int, Field(description="Maximum results to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Search for topics using GitHub's search API.
    
    This function searches GitHub topics, returning topic information including
    descriptions, creation details, and curation status.
    
    Args:
        query: Search query for topics
        limit: Maximum results to return
        
    Returns:
        List[Dict[str, Any]]: List of topic search results
        
    Example:
        >>> topics = search_topics("machine learning")
        >>> print(f"Found {len(topics)} topics related to machine learning")
    """
    return _search_topics_impl(query=query, limit=limit)

def list_repositories(
    org: Annotated[Optional[str], Field(description="Organization name (if None, lists user repos)", default=None)] = None,
    type: Annotated[str, Field(description="Repository type: 'all', 'public', 'private', 'member'", default="all")] = "all",
    sort: Annotated[str, Field(description="Sort order: 'created', 'updated', 'pushed', 'full_name'", default="updated")] = "updated",
    limit: Annotated[int, Field(description="Maximum number of repositories to return", ge=1, le=1000, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    List repositories in an organization or for authenticated user.
    
    🚀 Smart Fallback: If 'org' is not found as an organization, automatically 
    tries to list repositories for that user instead. Perfect for AI agents that 
    might confuse usernames with organization names!
    
    Args:
        org: Organization name or username (if None, lists authenticated user repos)
        type: Repository type ('all', 'public', 'private', 'member')
        sort: Sort order ('created', 'updated', 'pushed', 'full_name')
        limit: Maximum number of repositories to return
        
    Returns:
        List[Dict[str, Any]]: List of repository information objects
        
    Examples:
        # These all work intelligently:
        repos = list_repositories(org="pytorch")        # Organization
        repos = list_repositories(org="batteryshark")   # User (fallback)
        repos = list_repositories()                     # Authenticated user
    """
    return _list_repositories_impl(org=org, type=type, sort=sort, limit=limit)

def get_repository_info(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific repository.
    
    Args:
        repo_name: Repository name
        org: Organization name
        
    Returns:
        Optional[Dict[str, Any]]: Repository information or None if not found
    """
    return _get_repository_info_impl(repo_name, org)

def get_contributors(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum number of contributors to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Get contributor information for a repository.
    
    Args:
        repo_name: Repository name
        org: Organization name
        limit: Maximum number of contributors to return
        
    Returns:
        List[Dict[str, Any]]: List of contributor information
    """
    return _get_contributors_impl(repo_name, org, limit)

def get_repository_tree(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    recursive: Annotated[bool, Field(description="Whether to get full tree recursively", default=True)] = True
) -> Dict[str, Any]:
    """
    Get complete file tree of repository as nested dictionary.
    
    Args:
        repo_name: Repository name
        org: Organization name
        branch: Branch name (defaults to default branch)
        recursive: Whether to get full tree recursively
        
    Returns:
        Dict[str, Any]: Nested dictionary representing file structure
    """
    return _get_repository_tree_impl(repo_name, org, branch, recursive)

def get_repository_tree_ascii(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    show_file_sizes: Annotated[bool, Field(description="Whether to show file sizes in the tree", default=True)] = True,
    max_depth: Annotated[int, Field(description="Maximum depth to show (0 for unlimited)", ge=0, le=20, default=10)] = 10,
    sort_by: Annotated[str, Field(description="Sort order: 'name', 'size', 'type'", default="name")] = "name"
) -> str:
    """
    Get repository structure as ASCII tree visualization.
    
    Perfect for AI agents to quickly understand project organization.
    Similar to the Unix 'tree' command output.
    
    Args:
        repo_name: Repository name
        org: Organization name
        branch: Branch name (defaults to default branch)
        show_file_sizes: Whether to show file sizes in the tree
        max_depth: Maximum depth to show (0 for unlimited)
        sort_by: Sort order ('name', 'size', 'type')
        
    Returns:
        str: ASCII tree representation of repository structure
    """
    return _get_repository_tree_ascii_impl(repo_name=repo_name, org=org, branch=branch, show_file_sizes=show_file_sizes, max_depth=max_depth, sort_by=sort_by)

def list_directory(
    repo_name: Annotated[str, Field(description="Repository name")],
    directory_path: Annotated[str, Field(description="Path to directory (empty string for root)", default="")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None
) -> List[Dict[str, Any]]:
    """
    List contents of a specific directory in repository.
    
    This is like doing 'ls' or 'dir' on a specific path in the repository.
    Much more efficient than get_repository_tree() when you only need 
    the contents of one directory.
    
    Args:
        repo_name: Repository name
        directory_path: Path to directory (empty string for root)
        org: Organization name
        branch: Branch name (defaults to default branch)
        
    Returns:
        List[Dict[str, Any]]: List of directory contents with metadata
    """
    return _list_directory_impl(repo_name, directory_path, org, branch)

def get_file(
    repo_name: Annotated[str, Field(description="Repository name")],
    file_path: Annotated[str, Field(description="Path to file in repository")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    decode_content: Annotated[bool, Field(description="Whether to decode base64 content", default=True)] = True
) -> Optional[Dict[str, Any]]:
    """
    Get a specific file from repository.
    
    Args:
        repo_name: Repository name
        file_path: Path to file in repository
        org: Organization name
        branch: Branch name (defaults to default branch)
        decode_content: Whether to decode base64 content
        
    Returns:
        Optional[Dict[str, Any]]: File information with content or None if not found
    """
    return _get_file_impl(repo_name, file_path, org, branch, decode_content)

def get_files_as_codeblock(
    repo_name: Annotated[str, Field(description="Repository name")],
    file_paths: Annotated[List[str], Field(description="List of file paths (supports glob patterns)")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    support_globs: Annotated[bool, Field(description="Whether to expand glob patterns in file_paths", default=True)] = True,
    include_line_numbers: Annotated[bool, Field(description="Whether to include line numbers in output", default=False)] = False
) -> str:
    """
    Fetch multiple files and return them as a stitched codeblock format.
    
    Perfect for AI agents that need to analyze multiple files together.
    Returns files in code2prompt style format with file paths as headers
    and properly formatted code blocks.
    
    Args:
        repo_name: Repository name
        file_paths: List of file paths (supports glob patterns if support_globs=True)
        org: Organization name
        branch: Branch name (defaults to default branch)
        support_globs: Whether to expand glob patterns in file_paths
        include_line_numbers: Whether to include line numbers in output
        
    Returns:
        str: Formatted string with all files stitched together
    """
    return _get_files_as_codeblock_impl(repo_name, file_paths, org, branch, support_globs, include_line_numbers)

def get_pull_requests(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    state: Annotated[str, Field(description="PR state: 'open', 'closed', 'all'", default="open")] = "open",
    limit: Annotated[int, Field(description="Maximum number of PRs to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Get pull request information for repository.
    
    Args:
        repo_name: Repository name
        org: Organization name
        state: PR state ('open', 'closed', 'all')
        limit: Maximum number of PRs to return
        
    Returns:
        List[Dict[str, Any]]: List of pull request information
    """
    return _get_pull_requests_impl(repo_name, org, state, limit)

def get_commits(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum number of commits to return", ge=1, le=200, default=50)] = 50,
    since: Annotated[Optional[str], Field(description="Only commits after this date (ISO format)", default=None)] = None
) -> List[Dict[str, Any]]:
    """
    Get commit information for repository.
    
    Args:
        repo_name: Repository name
        org: Organization name
        branch: Branch name (defaults to default branch)
        limit: Maximum number of commits to return
        since: Only commits after this date (ISO format)
        
    Returns:
        List[Dict[str, Any]]: List of commit information
    """
    return _get_commits_impl(repo_name, org, branch, limit, since)

def get_issues(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    state: Annotated[str, Field(description="Issue state: 'open', 'closed', 'all'", default="open")] = "open",
    labels: Annotated[Optional[List[str]], Field(description="Filter by labels", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum number of issues to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Get issues for repository.
    
    Args:
        repo_name: Repository name
        org: Organization name
        state: Issue state ('open', 'closed', 'all')
        labels: Filter by labels
        limit: Maximum number of issues to return
        
    Returns:
        List[Dict[str, Any]]: List of issue information
    """
    return _get_issues_impl(repo_name, org, state, labels, limit)

def get_discussions(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum number of discussions to return", ge=1, le=200, default=50)] = 50
) -> List[Dict[str, Any]]:
    """
    Get discussions for repository.
    
    Note: This requires the repository to have discussions enabled.
    Uses GraphQL API which has different rate limits.
    
    Args:
        repo_name: Repository name
        org: Organization name
        limit: Maximum number of discussions to return
        
    Returns:
        List[Dict[str, Any]]: List of discussion information
    """
    return _get_discussions_impl(repo_name, org, limit)

# =============================================================================
# ENHANCED FILE SELECTION TOOLS
# =============================================================================

def get_repository_files_selective(
    repo_name: Annotated[str, Field(description="Repository name")],
    file_patterns: Annotated[List[str], Field(description="List of file paths or glob patterns (e.g., ['*.py', 'README.md', 'src/**/*.js'])")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    format_as_codeblock: Annotated[bool, Field(description="Whether to format as code blocks", default=True)] = True
) -> str:
    """
    Get selected files from repository using glob patterns with enhanced formatting.
    
    This tool provides sophisticated file selection using glob patterns and returns
    the content formatted for optimal LLM consumption. Much more flexible than the
    basic get_files_as_codeblock function.
    
    Args:
        repo_name: Repository name
        file_patterns: List of file paths or glob patterns (e.g., ['*.py', 'README.md', 'src/**/*.js'])
        org: Organization name
        branch: Branch name (defaults to default branch)
        format_as_codeblock: Whether to format as code blocks with syntax highlighting
        
    Returns:
        str: Selected files formatted as requested
        
    Example:
        >>> content = get_repository_files_selective("pytorch", ["torch/**/*.py", "setup.py"])
        >>> print("Selected PyTorch Python files retrieved and formatted")
    """
    return _get_repository_files_selective_impl(repo_name, file_patterns, org, branch, format_as_codeblock)

def get_code_snippets(
    repo_name: Annotated[str, Field(description="Repository name")],
    file_specs: Annotated[List[str], Field(description="List of file specifications with ranges (e.g., ['main.py:10-50', 'utils.py@100-500', 'config.py'])")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    format_as_codeblock: Annotated[bool, Field(description="Whether to format as code blocks", default=True)] = True
) -> str:
    """
    Extract specific code snippets from files with line or character ranges.
    
    This tool provides precise code extraction using line ranges (file.py:10-20) or
    character ranges (file.py@100-500). Perfect for getting specific functions,
    classes, or code sections without retrieving entire files.
    
    Args:
        repo_name: Repository name
        file_specs: List of file specifications with ranges:
                   - "file.py" (entire file)
                   - "file.py:10-20" (lines 10 to 20, 1-indexed)
                   - "file.py@100-500" (characters 100 to 500, 0-indexed)
        org: Organization name
        branch: Branch name (defaults to default branch)
        format_as_codeblock: Whether to format as code blocks with syntax highlighting
        
    Returns:
        str: Code snippets formatted as requested
        
    Example:
        >>> snippets = get_code_snippets("repo", ["main.py:1-50", "utils.py:100-200"])
        >>> print("Extracted specific code sections")
    """
    return _get_code_snippets_impl(repo_name, file_specs, org, branch, format_as_codeblock)

def get_files_bulk_data(
    repo_name: Annotated[str, Field(description="Repository name")],
    file_specs: Annotated[List[str], Field(description="List of file specifications with optional ranges")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None
) -> List[Dict[str, Any]]:
    """
    Fetch multiple files and return as structured data for MCP tools.
    
    This tool returns file data as structured objects rather than formatted text,
    making it perfect for MCP tools that need to process file metadata and content
    programmatically.
    
    Args:
        repo_name: Repository name
        file_specs: List of file specifications with optional ranges (same format as get_code_snippets)
        org: Organization name
        branch: Branch name (defaults to default branch)
        
    Returns:
        List[Dict[str, Any]]: List of file objects with path, content, size, language, range_info, etc.
        
    Example:
        >>> files = get_files_bulk_data("repo", ["*.py", "README.md:1-20"])
        >>> for file in files:
        ...     print(f"File: {file['path']}, Language: {file['language']}")
    """
    return _get_files_bulk_data_impl(repo_name, file_specs, org, branch)

def resolve_file_patterns(
    repo_name: Annotated[str, Field(description="Repository name")],
    file_patterns: Annotated[List[str], Field(description="List of file patterns to resolve")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None
) -> List[str]:
    """
    Resolve glob patterns to actual file paths in repository.
    
    This utility tool helps you see what files match your patterns before
    retrieving their content. Useful for exploring large repositories and
    understanding what files exist.
    
    Args:
        repo_name: Repository name
        file_patterns: List of file patterns or globs to resolve
        org: Organization name
        branch: Branch name (defaults to default branch)
        
    Returns:
        List[str]: List of resolved file paths that match the patterns
        
    Example:
        >>> files = resolve_file_patterns("pytorch", ["torch/**/*.py"])
        >>> print(f"Found {len(files)} Python files in torch directory")
    """
    return _resolve_file_patterns_impl(repo_name, file_patterns, org, branch)

# =============================================================================
# LOCAL CLONING TOOLS (NEW)
# =============================================================================

def clone_repository(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch to clone (defaults to default branch)", default=None)] = None,
    depth: Annotated[Optional[int], Field(description="Clone depth (1 for shallow clone, None for full clone)", default=1)] = 1,
    recurse_submodules: Annotated[bool, Field(description="Whether to recursively clone submodules", default=False)] = False,
    force_reclone: Annotated[bool, Field(description="Force re-clone even if already exists", default=False)] = False
) -> Optional[Dict[str, Any]]:
    """
    Clone a repository to local temporary directory for efficient bulk operations.
    
    🚀 **Perfect for Code Review Automation!** 
    Clone once, then access many files without API rate limit concerns.
    
    **NEW: Submodule Support!** 
    Use `recurse_submodules=True` to include all Git submodules in the clone.
    
    Args:
        repo_name: Repository name
        org: Organization name
        branch: Branch to clone (defaults to default branch)
        depth: Clone depth (1 for shallow clone, None for full clone)
        recurse_submodules: Whether to recursively clone submodules
        force_reclone: Force re-clone even if already exists
        
    Returns:
        Optional[Dict[str, Any]]: Clone information with path and metadata, or None if failed
        
    Example:
        >>> # Regular clone (fastest)
        >>> clone_info = clone_repository("pytorch", org="pytorch", depth=1)
        
        >>> # Clone with submodules (for complete analysis)
        >>> clone_info = clone_repository("pytorch", org="pytorch", depth=1, recurse_submodules=True)
        
        >>> if clone_info:
        ...     print(f"Cloned to: {clone_info['clone_path']}")
        ...     print(f"With submodules: {clone_info['with_submodules']}")
    """
    return _clone_repository_impl(repo_name, org, branch, depth, recurse_submodules, force_reclone)

def get_files_from_clone(
    repo_name: Annotated[str, Field(description="Repository name")],
    file_patterns: Annotated[List[str], Field(description="List of glob patterns to match files")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None,
    recurse_submodules: Annotated[bool, Field(description="Whether to clone submodules if not already cloned", default=False)] = False,
    format_as_codeblock: Annotated[bool, Field(description="Whether to format as code blocks", default=True)] = True
) -> str:
    """
    Get files from local clone using glob patterns (much faster than API for bulk operations).
    
    🚀 **Optimized for Code Review!** 
    Uses local file system for lightning-fast access to multiple files.
    Automatically clones repository if not already available.
    
    **NEW: Submodule Control!**
    Use `recurse_submodules=True` to ensure submodules are included when auto-cloning.
    
    Args:
        repo_name: Repository name
        file_patterns: List of glob patterns (e.g., ['*.py', 'src/**/*.js'])
        org: Organization name
        branch: Branch name
        recurse_submodules: Whether to clone submodules if repository needs to be cloned
        format_as_codeblock: Whether to format as code blocks with syntax highlighting
        
    Returns:
        str: Files formatted as code blocks or structured text
        
    Example:
        >>> # Get all Python files from a cloned repo (super fast!)
        >>> python_code = get_files_from_clone("pytorch", ["torch/**/*.py"], org="pytorch")
        
        >>> # Get files including submodules
        >>> all_code = get_files_from_clone("pytorch", ["**/*.py"], org="pytorch", recurse_submodules=True)
    """
    return _get_files_from_clone_impl(repo_name, file_patterns, org, branch, recurse_submodules, format_as_codeblock)

def cleanup_clone(
    repo_name: Annotated[str, Field(description="Repository name")],
    org: Annotated[Optional[str], Field(description="Organization name", default=None)] = None,
    branch: Annotated[Optional[str], Field(description="Branch name (defaults to default branch)", default=None)] = None
) -> bool:
    """
    Clean up a specific repository clone to free disk space.
    
    Args:
        repo_name: Repository name
        org: Organization name  
        branch: Branch name
        
    Returns:
        bool: True if successfully cleaned up
        
    Example:
        >>> cleanup_clone("pytorch", org="pytorch")
        True
    """
    return _cleanup_clone_impl(repo_name, org, branch)

def get_clone_status() -> Dict[str, Any]:
    """
    Get status of all active repository clones.
    
    Returns:
        Dict[str, Any]: Status information including active clones, total size, etc.
        
    Example:
        >>> status = get_clone_status()
        >>> print(f"Active clones: {status['active_clones']}")
        >>> print(f"Total size: {status['total_size_mb']}MB")
    """
    return _get_clone_status_impl()

# =============================================================================
# FILE HISTORY & FORENSIC ANALYSIS TOOLS (NEW)
# =============================================================================

def get_file_at_commit(
    file_path: Annotated[str, Field(description="Path to file within repository")],
    commit_hash: Annotated[str, Field(description="Commit hash to retrieve file from")],
    git_folder_path: Annotated[str, Field(description="Path to git repository directory", default=".")] = "."
) -> Optional[Dict[str, Any]]:
    """
    Get file content at a specific commit (perfect for bug investigation).
    
    🔍 **Perfect for Bug Investigation!**
    Retrieve any file as it existed at a specific point in history.
    Essential for tracking down when bugs were introduced or features changed.
    
    Args:
        file_path: Path to file within repository (e.g., "src/main.py")
        commit_hash: Commit hash to retrieve file from (can be short hash)
        git_folder_path: Path to git repository directory
        
    Returns:
        Dict with file content and commit information, or None if not found
        
    Example:
        >>> # Get a file from 3 commits ago to see old implementation
        >>> old_version = get_file_at_commit("src/search.py", "HEAD~3")
        >>> if old_version:
        ...     print(f"File as of commit {old_version['commit_info']['message']}")
        ...     print(old_version['content'])
    """
    return _get_file_at_commit_impl(git_folder_path, file_path, commit_hash)

def get_file_history(
    file_path: Annotated[str, Field(description="Path to file within repository")],
    git_folder_path: Annotated[str, Field(description="Path to git repository directory", default=".")] = ".",
    limit: Annotated[int, Field(description="Maximum number of commits to analyze", ge=1, le=200, default=50)] = 50,
    include_patches: Annotated[bool, Field(description="Whether to include detailed patches/diffs", default=False)] = False
) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive history of changes to a specific file.
    
    🕵️ **Perfect for Code Archaeology!**
    Follow a file's complete evolution through time. See who changed what,
    when, and why. Essential for understanding code evolution and finding
    when specific features or bugs were introduced.
    
    Args:
        file_path: Path to file within repository
        git_folder_path: Path to git repository directory
        limit: Maximum number of commits to analyze
        include_patches: Whether to include detailed patches/diffs for each commit
        
    Returns:
        Dict with comprehensive file history including all commits that touched this file
        
    Example:
        >>> # Investigate when a critical function was last changed
        >>> history = get_file_history("src/auth.py", limit=20, include_patches=True)
        >>> print(f"File changed {history['total_commits']} times")
        >>> for commit in history['commits'][:3]:
        ...     print(f"  {commit['date']}: {commit['message']} by {commit['author_name']}")
    """
    return _get_file_history_impl(git_folder_path, file_path, limit, include_patches)

def get_file_blame(
    file_path: Annotated[str, Field(description="Path to file within repository")],
    git_folder_path: Annotated[str, Field(description="Path to git repository directory", default=".")] = ".",
    commit_hash: Annotated[Optional[str], Field(description="Specific commit to blame (defaults to HEAD)", default=None)] = None
) -> Optional[Dict[str, Any]]:
    """
    Get git blame information showing who changed each line (perfect for accountability).
    
    👤 **Perfect for Code Ownership!**
    See who wrote or last modified every single line in a file.
    Essential for finding the right person to ask about specific code,
    or tracking down who introduced a particular bug or feature.
    
    Args:
        file_path: Path to file within repository
        git_folder_path: Path to git repository directory
        commit_hash: Specific commit to blame (defaults to current HEAD)
        
    Returns:
        Dict with line-by-line blame information including author, date, and commit
        
    Example:
        >>> # Find out who wrote each line of a buggy function
        >>> blame = get_file_blame("src/payment.py")
        >>> for line in blame['blame_lines']:
        ...     if 'calculate_total' in line['content']:
        ...         print(f"Line {line['line_number']}: {line['author']} on {line['date']}")
        ...         print(f"  Code: {line['content']}")
        ...         print(f"  Commit: {line['summary']}")
    """
    return _get_file_blame_impl(git_folder_path, file_path, commit_hash)

def search_file_changes(
    file_path: Annotated[str, Field(description="Path to file within repository")],
    search_term: Annotated[str, Field(description="Code or text to search for in file history")],
    git_folder_path: Annotated[str, Field(description="Path to git repository directory", default=".")] = ".",
    context_lines: Annotated[int, Field(description="Number of context lines around matches", ge=0, le=10, default=3)] = 3
) -> Optional[Dict[str, Any]]:
    """
    Search for when specific code/text was added or removed from a file.
    
    🔍 **Perfect for Bug Archaeology!**
    Find exactly when specific code, functions, or text was added, modified,
    or removed. Essential for tracking down when bugs were introduced or
    when specific features were implemented.
    
    Args:
        file_path: Path to file within repository
        search_term: Code, function name, or text to search for
        git_folder_path: Path to git repository directory
        context_lines: Number of context lines around matches
        
    Returns:
        Dict with commits that added/removed the search term, plus commits mentioning it
        
    Example:
        >>> # Find when a specific function was added or modified
        >>> changes = search_file_changes("src/api.py", "def authenticate")
        >>> print(f"Found {changes['total_matches']} commits related to 'authenticate'")
        >>> 
        >>> for commit in changes['commits_with_code_changes']:
        ...     print(f"Code changed in: {commit['message']} by {commit['author']}")
        ...     print(f"Changes: {commit['changes']}")
    """
    return _search_file_changes_impl(git_folder_path, file_path, search_term, context_lines)

def compare_file_versions(
    file_path: Annotated[str, Field(description="Path to file within repository")],
    commit1: Annotated[str, Field(description="First commit to compare (older)")],
    git_folder_path: Annotated[str, Field(description="Path to git repository directory", default=".")] = ".",
    commit2: Annotated[str, Field(description="Second commit to compare (defaults to HEAD)", default="HEAD")] = "HEAD"
) -> Optional[Dict[str, Any]]:
    """
    Compare two versions of a file between commits (perfect for regression analysis).
    
    🔬 **Perfect for Regression Analysis!**
    See exactly what changed in a file between any two points in history.
    Essential for understanding how bugs were introduced or how features evolved.
    
    Args:
        file_path: Path to file within repository
        commit1: First commit to compare (older version)
        git_folder_path: Path to git repository directory
        commit2: Second commit to compare (newer version, defaults to HEAD)
        
    Returns:
        Dict with detailed diff and metadata about both commits
        
    Example:
        >>> # Compare current version with version from last week
        >>> comparison = compare_file_versions("src/core.py", "HEAD~7")
        >>> if comparison['has_changes']:
        ...     print(f"Changes between commits:")
        ...     print(f"  Old: {comparison['commit1']['message']}")
        ...     print(f"  New: {comparison['commit2']['message']}")
        ...     print(f"\\nDiff:\\n{comparison['diff']}")
        >>> else:
        ...     print("No changes to this file between these commits")
    """
    return _compare_file_versions_impl(git_folder_path, file_path, commit1, commit2)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [
        # Original GitHub browser tools
        search_files,
        search_content,
        list_repositories,
        get_repository_info,
        get_contributors,
        get_repository_tree,
        get_repository_tree_ascii,
        list_directory,
        get_file,
        get_files_as_codeblock,
        get_pull_requests,
        get_commits,
        get_issues,
        get_discussions,
        # Enhanced file selection tools
        get_repository_files_selective,
        get_code_snippets,
        get_files_bulk_data,
        resolve_file_patterns,
        # Local cloning tools
        clone_repository,
        get_files_from_clone,
        cleanup_clone,
        get_clone_status,
        # File history and forensic tools
        get_file_at_commit,
        get_file_history,
        get_file_blame,
        search_file_changes,
        compare_file_versions
    ],
    "init_function": [initialize_plugin]
}
# =============================================================================
# END OF EXPORTS
# ============================================================================= 