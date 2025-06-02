# Code Converter Plugin

A comprehensive plugin for converting between directory structures and prompt formats, with support for both local filesystem operations and GitHub repositories via API.

## Overview

This plugin provides AI agents with powerful tools to:
- Convert directory structures into single prompt files with all code stitched together
- Extract specific files or code snippets from projects 
- Work with GitHub repositories remotely via the GitHub API
- Convert prompt files back into directory structures
- Support for selective file inclusion using glob patterns and line/character ranges

Perfect for AI agents that need to analyze entire codebases, extract specific code sections, or work with remote repositories without local cloning.

## Installation

1. Install the plugin dependencies:
   ```bash
   pip install pydantic>=2.0.0 requests>=2.25.0 PyGithub>=1.59.0 urllib3>=1.26.0
   ```

2. Import the plugin in your agent framework

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | No | "" | GitHub personal access token or app token for API access |
| `GITHUB_BASE_URL` | No | `https://api.github.com` | GitHub API base URL (for GitHub Enterprise) |
| `GITHUB_ORG` | No | "" | Default GitHub organization to use when not specified |

### Setting up GitHub Access

1. **Personal Access Token**: Generate a token at https://github.com/settings/tokens
2. **Set Environment Variable**: `export GITHUB_TOKEN=your_token_here`
3. **Optional Org**: `export GITHUB_ORG=your_default_org` (optional)

For GitHub Enterprise, also set:
```bash
export GITHUB_BASE_URL=https://your-enterprise.github.com/api/v3
```

## Available Tools

### Local Directory Operations

#### `convert_directory_to_prompt(directory_path, output_path=None, ignore_patterns=None)`
Convert an entire directory structure into a prompt file.

**Example:**
```python
content = convert_directory_to_prompt("./my_project", "project.txt")
```

#### `convert_selected_files_to_prompt(file_patterns, base_dir=".", output_path=None)`
Convert only selected files using glob patterns.

**Example:**
```python
content = convert_selected_files_to_prompt(["*.py", "*.md"], "./project")
```

#### `extract_code_snippets(file_specs, base_dir=".", output_path=None)`
Extract specific code snippets with line or character ranges.

**Example:**
```python
snippets = extract_code_snippets([
    "main.py:1-50",        # Lines 1-50
    "utils.py@100-500",    # Characters 100-500
    "config.py"            # Entire file
])
```

### Prompt Conversion

#### `convert_prompt_to_directory(prompt_file_path, output_dir_path=None)`
Convert a prompt file back into directory structure.

**Example:**
```python
result = convert_prompt_to_directory("project.txt", "./reconstructed")
print(f"Created {result['files_created']} files")
```

### GitHub Operations

#### `convert_github_repository(repo_name, org=None, branch=None, output_path=None)`
Convert an entire GitHub repository to prompt format.

**Example:**
```python
content = convert_github_repository("pytorch", org="pytorch", branch="main")
```

#### `convert_github_selected_files(repo_name, file_patterns, org=None, branch=None, output_path=None)`
Convert selected files from a GitHub repository.

**Example:**
```python
content = convert_github_selected_files("repo", ["*.py", "README.md"], org="myorg")
```

#### `get_github_code_snippets(repo_name, file_specs, org=None, branch=None, output_path=None)`
Extract code snippets from GitHub repository files.

**Example:**
```python
snippets = get_github_code_snippets("repo", ["main.py:1-100"], org="myorg")
```

#### `get_github_files_bulk(repo_name, file_specs, org=None, branch=None)`
Fetch multiple files as structured data (perfect for MCP tools).

**Example:**
```python
files = get_github_files_bulk("repo", ["*.py"], org="myorg")
for file in files:
    print(f"File: {file['path']}, Size: {file['size']}")
```

## Usage Examples

### Analyze a Local Project
```python
# Convert entire project
content = convert_directory_to_prompt("./my_app")

# Or just the Python files
content = convert_selected_files_to_prompt(["*.py"], "./my_app")

# Or specific functions
snippets = extract_code_snippets([
    "main.py:1-50",
    "utils/helpers.py:100-200"
], "./my_app")
```

### Work with GitHub Repositories
```python
# Analyze a remote repository
content = convert_github_repository("fastapi", org="tiangolo")

# Get just the Python files
content = convert_github_selected_files("fastapi", ["*.py"], org="tiangolo")

# Extract specific code sections
snippets = get_github_code_snippets("fastapi", [
    "fastapi/main.py:1-100",
    "fastapi/routing.py:50-150"
], org="tiangolo")
```

### Convert Back to Files
```python
# Reconstruct a project from a prompt file
result = convert_prompt_to_directory("analyzed_project.txt", "./output")
print(f"Reconstructed {result['files_created']} files in {result['output_directory']}")
```

## File Specification Formats

The plugin supports flexible file specification formats:

### Basic Files
- `"file.py"` - Entire file
- `"path/to/file.js"` - File with path

### Line Ranges
- `"file.py:10-20"` - Lines 10 through 20
- `"file.py:10:20"` - Alternative syntax
- `"file.py:50"` - Just line 50

### Character Ranges
- `"file.py@100-500"` - Characters 100 through 500
- `"file.py@100:500"` - Alternative syntax

### Glob Patterns
- `"*.py"` - All Python files
- `"src/**/*.js"` - All JavaScript files in src/ recursively
- `"tests/test_*.py"` - All test files

## Output Format

The plugin generates prompt files in a standardized format:

```
__
Project Path: my_project

Source Tree:

```txt
my_project
├── README.md
├── main.py
└── utils/
    └── helpers.py
```

`README.md`:

```md
# My Project
Description here...
```

`main.py`:

```python
def main():
    print("Hello World")
```
```

## Error Handling

The plugin handles errors gracefully:
- Missing files return appropriate error messages
- Binary files are automatically skipped
- Large files (>1MB) are skipped in GitHub operations
- Network errors are caught and logged
- Invalid file specifications are validated

## Performance Considerations

- **Local Operations**: Fast for most projects, may be slower for very large directories
- **GitHub Operations**: Subject to GitHub API rate limits
- **File Size Limits**: GitHub operations skip files >1MB to prevent memory issues
- **Network Dependency**: GitHub features require internet connectivity

## Contributing

This plugin follows the ld-agent plugin specification. To contribute:

1. Ensure all code is self-contained within the plugin directory
2. Follow the established type annotation patterns
3. Add comprehensive docstrings to all public functions
4. Include appropriate error handling and logging
5. Test with both local and GitHub operations

## License

This plugin is provided as-is for use with ld-agent compatible systems. 