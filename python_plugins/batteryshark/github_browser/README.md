# GitHub Browser Plugin

Browse and explore GitHub repositories with AI-focused tools and enhanced file selection capabilities.

## What it does

**Core GitHub Operations:**
- Search for files by name across repositories or within specific repos
- Search for content within files using GitHub's search API
- **🆕 Search for issues and pull requests** with advanced filtering
- **🆕 Search for commits** by message, author, and committer
- **🆕 Search for repositories** by name, description, and language
- **🆕 Search for users and organizations** by profile information
- **🆕 Search for topics** across GitHub's topic system
- List repositories for organizations or users with detailed metadata
- Get repository information including languages, contributors, and statistics
- Browse repository file trees with ASCII visualization
- List directory contents and retrieve individual files
- Access pull requests, commits, issues, and discussions

**Enhanced File Selection (NEW):**
- **Selective file retrieval** using glob patterns (e.g., `*.py`, `src/**/*.js`)
- **Code snippet extraction** with line ranges (`file.py:10-20`) and character ranges (`file.py@100-500`)
- **Bulk file operations** returning structured data for MCP tools
- **Pattern resolution** to see what files match your globs before fetching
- **Optimized formatting** for LLM consumption with proper syntax highlighting

## Requirements

- Python 3.10+
- `PyGithub>=1.59.0`
- `pydantic>=2.0.0`
- `urllib3`
- Platform: any

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | No | "" | GitHub personal access token or app token |
| `GITHUB_USER_TOKEN` | No | "" | **NEW**: Personal access token for user-level operations |
| `GITHUB_AUTH_PREFERENCE` | No | "auto" | **NEW**: Authentication preference: 'app', 'user', or 'auto' |
| `GITHUB_BASE_URL` | No | `https://api.github.com` | GitHub API base URL (for Enterprise) |
| `GITHUB_ORG` | No | "" | Default organization when not specified |
| `GITHUB_APP_ID` | No | "" | GitHub App ID for app authentication |
| `GITHUB_PRIVATE_KEY_PATH` | No | "" | Path to GitHub App private key file |

## 🔐 Enhanced Authentication (NEW)

The GitHub Browser now supports **configurable authentication** that intelligently chooses between GitHub App and personal access token authentication:

- **GitHub App Auth**: Best for organization repositories, team access, enterprise deployments
- **Personal Token Auth**: Best for personal repositories, individual development  
- **Auto Mode**: Intelligently chooses the best auth method based on context

### Quick Setup for Personal Repos

```bash
export GITHUB_USER_TOKEN="your_personal_access_token"
export GITHUB_AUTH_PREFERENCE="user"
```

### Quick Setup for Mixed Usage (Recommended)

```bash
export GITHUB_USER_TOKEN="your_personal_token"
# Keep existing GitHub App configuration
export GITHUB_AUTH_PREFERENCE="auto"  # Default
```

**👉 See [AUTHENTICATION.md](./AUTHENTICATION.md) for detailed setup guide**

## 🚀 Local Cloning for Code Review Automation (NEW)

The GitHub Browser now supports **local repository cloning** for scenarios where you need to access many files efficiently, perfect for code review automation!

**🔥 NEW: Git Submodule Support!** Clone repositories with their submodules for complete project analysis.

### When to Use Local Cloning vs API

| Use Case | Recommended Method | Why |
|----------|-------------------|-----|
| **Single file access** | API | Faster for one-off requests |
| **Code review automation** | **Local Clone** | Much faster for bulk operations |
| **Analyzing 10+ files** | **Local Clone** | Avoids rate limits |
| **Cross-file analysis** | **Local Clone** | Full repository context |
| **Repeated file access** | **Local Clone** | Cache benefits |
| **Projects with submodules** | **Local Clone + Submodules** | Complete dependency analysis |

### Code Review Automation Example

```python
# Clone repository once for review (including submodules for complete analysis)
clone_info = clone_repository("pytorch", org="pytorch", depth=1, recurse_submodules=True)

# Now access many files super fast (no API calls!)
nn_modules = get_files_from_clone("pytorch", ["torch/nn/modules/*.py"], org="pytorch")
optimizers = get_files_from_clone("pytorch", ["torch/optim/*.py"], org="pytorch") 
tests = get_files_from_clone("pytorch", ["test/test_*.py"], org="pytorch")

# Access submodule files too!
submodule_code = get_files_from_clone("pytorch", ["third_party/**/*.py"], org="pytorch")

# Clean up when done
cleanup_clone("pytorch", org="pytorch")
```

### Smart Features

- **Auto-fallback**: If cloning fails, automatically uses API method
- **Intelligent caching**: Reuses existing clones when possible  
- **Safety limits**: Configurable max repository size (default 500MB)
- **Auto-cleanup**: Removes old clones after 24 hours by default
- **Resource monitoring**: Track disk usage and active clones
- **🆕 Submodule support**: Optional recursive cloning of Git submodules
- **🆕 Smart timeouts**: Longer timeouts for submodule operations

## 🔧 Git Submodule Support (NEW)

The GitHub Browser now includes comprehensive Git submodule support for complete project analysis.

### When to Use Submodules

| Project Type | Use Submodules | Why |
|--------------|----------------|-----|
| **Monorepos with dependencies** | ✅ Yes | Access all dependency code |
| **Projects with git submodules** | ✅ Yes | Complete project structure |
| **C++ projects with libs** | ✅ Yes | Analyze third-party libraries |
| **Simple Python packages** | ❌ Usually No | Faster without submodules |
| **Quick file inspection** | ❌ No | API is faster for single files |

### Performance Considerations

- **Size Impact**: Submodules can significantly increase clone size and time
- **Timeout Settings**: Submodule clones get longer timeouts (10 minutes vs 5 minutes)
- **Shallow Clones**: Uses `--shallow-submodules` with `depth=1` for efficiency
- **Cache Benefits**: Once cloned with submodules, subsequent operations are very fast

### Best Practices

```python
# ✅ Good: Clone with submodules for comprehensive analysis
clone_info = clone_repository("large-project", org="company", 
                             depth=1, recurse_submodules=True)

# ✅ Good: Use shallow clones for speed
clone_info = clone_repository("project", depth=1, recurse_submodules=True)

# ✅ Good: Clean up when done to save disk space
get_files_from_clone("project", ["**/*.py"], recurse_submodules=True)
cleanup_clone("project")

# ❌ Avoid: Full clone with submodules unless specifically needed
clone_info = clone_repository("project", depth=None, recurse_submodules=True)
```

### Submodule-Aware File Patterns

```python
# Access main repository files
main_files = get_files_from_clone("project", ["src/**/*.py"])

# Access specific submodule files  
sub_files = get_files_from_clone("project", ["third_party/lib/**/*.cpp"])

# Access all files including submodules
all_files = get_files_from_clone("project", ["**/*.py", "**/*.cpp"], recurse_submodules=True)
```

## Exported Functions

### Enhanced File Selection Tools (NEW)

#### `get_repository_files_selective(repo_name, file_patterns, org, branch, format_as_codeblock) -> str`
Get selected files from repository using sophisticated glob patterns.

**Perfect for:** Getting specific file types or directories without fetching the entire repository.

**Parameters:**
- `repo_name` (str): Repository name
- `file_patterns` (List[str]): Glob patterns (e.g., `['*.py', 'README.md', 'src/**/*.js']`)
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name
- `format_as_codeblock` (bool): Whether to format as code blocks with syntax highlighting

**Example:**
```python
# Get all Python files and the README
content = get_repository_files_selective(
    "pytorch", 
    ["torch/**/*.py", "README.md", "setup.py"],
    org="pytorch"
)
```

#### `get_code_snippets(repo_name, file_specs, org, branch, format_as_codeblock) -> str`
Extract specific code snippets with precise line or character ranges.

**Perfect for:** Getting specific functions, classes, or code sections without entire files.

**Parameters:**
- `repo_name` (str): Repository name
- `file_specs` (List[str]): File specifications with ranges:
  - `"file.py"` (entire file)
  - `"file.py:10-20"` (lines 10 to 20, 1-indexed)
  - `"file.py@100-500"` (characters 100 to 500, 0-indexed)
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name
- `format_as_codeblock` (bool): Whether to format as code blocks

**Example:**
```python
# Get specific code sections
snippets = get_code_snippets(
    "myrepo",
    ["main.py:1-50", "utils.py:100-200", "config.py@500-1000"],
    org="myorg"
)
```

#### `get_files_bulk_data(repo_name, file_specs, org, branch) -> List[Dict[str, Any]]`
Fetch multiple files and return as structured data for programmatic processing.

**Perfect for:** MCP tools that need file metadata and content as structured objects.

**Parameters:**
- `repo_name` (str): Repository name
- `file_specs` (List[str]): File specifications with optional ranges (same format as `get_code_snippets`)
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name

**Returns:** List of file objects with `path`, `content`, `size`, `language`, `range_info`, `sha`, etc.

#### `resolve_file_patterns(repo_name, file_patterns, org, branch) -> List[str]`
Resolve glob patterns to actual file paths without fetching content.

**Perfect for:** Exploring large repositories and understanding what files exist before fetching.

**Parameters:**
- `repo_name` (str): Repository name
- `file_patterns` (List[str]): Glob patterns to resolve
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name

**Returns:** List of resolved file paths

### Original GitHub Browser Tools

#### `search_files(query, repo, org, path, extension, limit) -> List[Dict[str, Any]]`
Search for files using GitHub's search API.

**Parameters:**
- `query` (str): Search query (filename or partial filename)
- `repo` (str, optional): Specific repository name
- `org` (str, optional): Organization name
- `path` (str, optional): Limit search to specific path
- `extension` (str, optional): File extension filter (e.g., 'py', 'js')
- `limit` (int): Maximum results to return (1-1000)

**Returns:** `List[Dict[str, Any]]` - List of file information objects

#### `search_content(query, repo, org, path, extension, limit) -> List[Dict[str, Any]]`
Search for content within files using GitHub's search API.

**Parameters:**
- `query` (str): Content to search for within files
- `repo` (str, optional): Specific repository name
- `org` (str, optional): Organization name
- `path` (str, optional): Limit search to specific path
- `extension` (str, optional): File extension filter
- `limit` (int): Maximum results to return (1-200)

**Returns:** `List[Dict[str, Any]]` - List of search results with content matches

#### `list_repositories(org, type, sort, limit) -> List[Dict[str, Any]]`
List repositories in an organization or for authenticated user.

**🚀 Smart Fallback:** Automatically tries user repositories if the provided 'org' isn't found as an organization. Perfect for AI agents that might confuse usernames with organization names!

**Parameters:**
- `org` (str, optional): Organization name or username (if None, lists authenticated user repos)
- `type` (str): Repository type ('all', 'public', 'private', 'member')
- `sort` (str): Sort order ('created', 'updated', 'pushed', 'full_name')
- `limit` (int, optional): Maximum number of repositories to return

**Returns:** `List[Dict[str, Any]]` - List of repository information objects

**Examples:**
```python
# These all work intelligently:
repos = list_repositories(org="pytorch")        # Organization
repos = list_repositories(org="batteryshark")   # User (auto-fallback)
repos = list_repositories()                     # Authenticated user
```

#### `get_repository_info(repo_name, org) -> Optional[Dict[str, Any]]`
Get detailed information about a specific repository.

**Parameters:**
- `repo_name` (str): Repository name
- `org` (str, optional): Organization name

**Returns:** `Optional[Dict[str, Any]]` - Repository information or None if not found

#### `get_repository_tree_ascii(repo_name, org, branch, show_file_sizes, max_depth, sort_by) -> str`
Get repository structure as ASCII tree visualization.

**Parameters:**
- `repo_name` (str): Repository name
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name
- `show_file_sizes` (bool): Whether to show file sizes in the tree
- `max_depth` (int, optional): Maximum depth to show
- `sort_by` (str): Sort order ('name', 'size', 'type')

**Returns:** `str` - ASCII tree representation of repository structure

#### `get_file(repo_name, file_path, org, branch, decode_content) -> Optional[Dict[str, Any]]`
Get a specific file from repository.

**Parameters:**
- `repo_name` (str): Repository name
- `file_path` (str): Path to file in repository
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name
- `decode_content` (bool): Whether to decode base64 content

**Returns:** `Optional[Dict[str, Any]]` - File information with content or None

#### `get_files_as_codeblock(repo_name, file_paths, org, branch, support_globs, include_line_numbers) -> str`
Fetch multiple files and return them as a stitched codeblock format.

**Parameters:**
- `repo_name` (str): Repository name
- `file_paths` (List[str]): List of file paths (supports glob patterns)
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name
- `support_globs` (bool): Whether to expand glob patterns
- `include_line_numbers` (bool): Whether to include line numbers

**Returns:** `str` - Formatted string with all files stitched together

#### Additional tools: `get_contributors`, `get_repository_tree`, `list_directory`, `get_pull_requests`, `get_commits`, `get_issues`, `get_discussions`

### Local Cloning Tools (NEW)

#### `clone_repository(repo_name, org, branch, depth, recurse_submodules, force_reclone) -> Optional[Dict[str, Any]]`
Clone a repository to local temporary directory for efficient bulk operations.

**🚀 Perfect for Code Review Automation!**

**🆕 Now with Git Submodule Support!** Use `recurse_submodules=True` for complete project analysis.

**Parameters:**
- `repo_name` (str): Repository name
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch to clone (defaults to default branch)
- `depth` (int, optional): Clone depth (1 for shallow clone, None for full clone)
- `recurse_submodules` (bool): Whether to recursively clone submodules
- `force_reclone` (bool): Force re-clone even if already exists

**Returns:** `Optional[Dict[str, Any]]` - Clone information with path and metadata

**Examples:**
```python
# Regular shallow clone (fastest)
clone_info = clone_repository("pytorch", org="pytorch", depth=1)

# Clone with submodules for complete analysis  
clone_info = clone_repository("pytorch", org="pytorch", depth=1, recurse_submodules=True)

# Full clone with submodules
clone_info = clone_repository("myrepo", org="myorg", depth=None, recurse_submodules=True)
```

#### `get_files_from_clone(repo_name, file_patterns, org, branch, recurse_submodules, format_as_codeblock) -> str`
Get files from local clone using glob patterns (much faster than API for bulk operations).

**🚀 Optimized for Code Review!** Lightning-fast access to multiple files.

**🆕 Submodule Control!** Use `recurse_submodules=True` when auto-cloning to include submodules.

**Parameters:**
- `repo_name` (str): Repository name
- `file_patterns` (List[str]): List of glob patterns (e.g., `['*.py', 'src/**/*.js']`)
- `org` (str, optional): Organization name
- `branch` (str, optional): Branch name
- `recurse_submodules` (bool): Whether to clone submodules if repository needs to be cloned
- `format_as_codeblock` (bool): Whether to format as code blocks

**Returns:** `str` - Files formatted as code blocks or structured text

**Examples:**
```python
# Get files from existing clone or create regular clone
files = get_files_from_clone("pytorch", ["torch/**/*.py"], org="pytorch")

# Auto-clone with submodules if needed for complete file access
files = get_files_from_clone("pytorch", ["**/*.py"], org="pytorch", recurse_submodules=True)
```

#### `cleanup_clone(repo_name, org, branch) -> bool`
Clean up a specific repository clone to free disk space.

#### `get_clone_status() -> Dict[str, Any]`
Get status of all active repository clones including disk usage.

### Enhanced Search Tools (NEW)

#### `search_issues(query, repo, org, state, labels, sort, order, limit) -> List[Dict[str, Any]]`
Search for issues and pull requests using GitHub's search API.

**Perfect for:** Finding bugs, feature requests, discussions, and pull requests across repositories.

**Parameters:**
- `query` (str): Search query for issues and pull requests
- `repo` (str, optional): Specific repository name
- `org` (str, optional): Organization name
- `state` (str, optional): Issue state ('open', 'closed')
- `labels` (List[str], optional): List of label names to filter by
- `sort` (str, optional): Sort order ('comments', 'created', 'updated')
- `order` (str, optional): Order ('asc', 'desc')
- `limit` (int): Maximum results to return

**Example:**
```python
# Find open bugs in a specific repository
bugs = search_issues("type:issue state:open label:bug", repo="pytorch", org="pytorch")

# Search for PRs by a specific author
prs = search_issues("type:pr author:username", org="pytorch")
```

#### `search_commits(query, repo, org, author, committer, sort, order, limit) -> List[Dict[str, Any]]`
Search for commits using GitHub's search API.

**Perfect for:** Finding specific commits by message content, author, or committer.

**Parameters:**
- `query` (str): Search query for commits
- `repo` (str, optional): Specific repository name
- `org` (str, optional): Organization name
- `author` (str, optional): Commit author
- `committer` (str, optional): Commit committer
- `sort` (str, optional): Sort order ('author-date', 'committer-date')
- `order` (str, optional): Order ('asc', 'desc')
- `limit` (int): Maximum results to return

**Example:**
```python
# Find bug fix commits
fixes = search_commits("fix bug", repo="pytorch", org="pytorch")

# Search commits by specific author
commits = search_commits("optimization", author="username", org="pytorch")
```

#### `search_repositories(query, org, language, sort, order, limit) -> List[Dict[str, Any]]`
Search for repositories using GitHub's search API.

**Perfect for:** Discovering repositories by topic, technology, or organization.

**Parameters:**
- `query` (str): Search query for repositories
- `org` (str, optional): Organization name
- `language` (str, optional): Programming language filter
- `sort` (str, optional): Sort order ('stars', 'forks', 'updated')
- `order` (str, optional): Order ('asc', 'desc')
- `limit` (int): Maximum results to return

**Example:**
```python
# Find popular machine learning repositories
ml_repos = search_repositories("machine learning", language="python", sort="stars")

# Search within an organization
org_repos = search_repositories("neural network", org="pytorch")
```

#### `search_users(query, type, sort, order, limit) -> List[Dict[str, Any]]`
Search for users and organizations using GitHub's search API.

**Perfect for:** Finding developers, organizations, or contributors by expertise.

**Parameters:**
- `query` (str): Search query for users
- `type` (str, optional): User type ('user', 'org')
- `sort` (str, optional): Sort order ('followers', 'repositories', 'joined')
- `order` (str, optional): Order ('asc', 'desc')
- `limit` (int): Maximum results to return

**Example:**
```python
# Find users interested in machine learning
ml_users = search_users("machine learning", type="user", sort="followers")

# Search for organizations
orgs = search_users("university", type="org")
```

#### `search_topics(query, limit) -> List[Dict[str, Any]]`
Search for topics using GitHub's search API.

**Perfect for:** Discovering GitHub topics and understanding trending technologies.

**Parameters:**
- `query` (str): Search query for topics
- `limit` (int): Maximum results to return

**Example:**
```python
# Find topics related to web development
web_topics = search_topics("web development")

# Search for AI/ML topics
ai_topics = search_topics("artificial intelligence")
```

## Usage Examples

### Enhanced File Selection

```python
from github_browser import get_repository_files_selective, get_code_snippets, resolve_file_patterns

# Get all Python files in a specific directory
python_files = get_repository_files_selective(
    "pytorch", 
    ["torch/nn/**/*.py"], 
    org="pytorch"
)

# Extract specific functions from multiple files
code_snippets = get_code_snippets(
    "pytorch",
    [
        "torch/nn/modules/linear.py:1-100",  # First 100 lines
        "torch/nn/functional.py:200-300",    # Lines 200-300
        "setup.py@0-1000"                    # First 1000 characters
    ],
    org="pytorch"
)

# See what files match a pattern before fetching
matching_files = resolve_file_patterns(
    "pytorch",
    ["torch/**/*.py", "test/**/*.py"],
    org="pytorch"
)
print(f"Found {len(matching_files)} Python files")
```

### Traditional Operations

```python
from github_browser import search_files, get_repository_info, get_file

# Search for Python files
files = search_files("neural", extension="py", limit=10)

# Get repository information
repo_info = get_repository_info("pytorch", org="pytorch")

# Get a specific file
file_content = get_file("pytorch", "README.md", org="pytorch")
```

### Enhanced Search Examples

```python
from github_browser import (
    search_issues, search_commits, search_repositories, 
    search_users, search_topics
)

# Comprehensive issue search across multiple criteria
critical_issues = search_issues(
    "memory leak OR performance issue", 
    repo="pytorch", 
    org="pytorch",
    state="open",
    labels=["high priority", "bug"],
    sort="updated"
)

# Find recent commits by core maintainers
recent_commits = search_commits(
    "fix OR improve", 
    repo="pytorch",
    org="pytorch",
    sort="committer-date",
    order="desc"
)

# Discover trending ML repositories
trending_ml = search_repositories(
    "deep learning transformer", 
    language="python",
    sort="stars",
    order="desc"
)

# Find AI researchers and organizations
ai_experts = search_users(
    "artificial intelligence researcher", 
    sort="followers",
    order="desc"
)

# Explore trending topics in AI
ai_topics = search_topics("neural network")
```

## Setup GitHub Access

1. Generate a GitHub personal access token at https://github.com/settings/tokens
2. Set `GITHUB_TOKEN` environment variable
3. Optionally set `GITHUB_ORG` for default organization

## Key Advantages for LLMs

1. **Precise Code Extraction**: Get exactly the code you need with line/character ranges
2. **Smart Pattern Matching**: Use glob patterns to select relevant files efficiently  
3. **Optimized Formatting**: Code blocks with proper syntax highlighting for better understanding
4. **Bulk Operations**: Structured data output perfect for programmatic processing
5. **Repository Exploration**: Understand project structure before diving into specific files
