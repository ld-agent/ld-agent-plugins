"""
Example usage of the ripgrep plugin with explicit initialization.

This demonstrates how to use the new configuration-driven approach for
both local development and remote deployment scenarios.
"""

import asyncio
from pathlib import Path

# Import the plugin
from ripgrep_plugin import (
    initialize_ripgrep_plugin,
    search_pattern,
    find_symbol,
    search_files,
    get_file_context,
    analyze_codebase,
)


def example_local_development():
    """Example: Setting up plugin for local development."""
    print("=== Local Development Mode ===")
    
    # Initialize for local development
    # This would typically be done once when the plugin is loaded
    initialize_ripgrep_plugin(
        mode="local",
        workspace_root="/Users/developer/my-project",  # Explicit project root
        max_results=150,  # Higher limits for local use
        max_filesize="50M",  # Larger files allowed locally
        timeout_seconds=60,  # Longer timeout for local use
    )
    
    # Now use the tools
    results = search_pattern("class.*Controller", file_types=["py", "js"])
    print(f"Found {results['results']['total_matches']} controller classes")


def example_local_auto_workspace():
    """Example: Auto-detect workspace for local development."""
    print("=== Local Auto-Workspace Mode ===")
    
    # Initialize with minimal config - will auto-detect current workspace
    initialize_ripgrep_plugin(
        mode="local",
        # No workspace_root specified - will use current directory
    )
    
    # Search in the detected workspace
    files = search_files(name_pattern="*.md")
    print(f"Found {files['results']['total_files']} markdown files")


def example_remote_single_tenant():
    """Example: Remote deployment with single tenant."""
    print("=== Remote Single-Tenant Mode ===")
    
    # Initialize for remote single-tenant deployment
    initialize_ripgrep_plugin(
        mode="remote",
        workspace_root="/app/workspace",  # Server-controlled workspace
        max_results=50,  # Conservative limits for remote
        max_filesize="5M",  # Smaller files for remote
        timeout_seconds=15,  # Faster timeout for remote
    )
    
    # Tools automatically use the restricted configuration
    analysis = analyze_codebase()
    print(f"Analyzed codebase: {analysis['results']['summary']}")


def example_remote_multi_tenant():
    """Example: Remote deployment with multi-tenancy."""
    print("=== Remote Multi-Tenant Mode ===")
    
    # This would be called by the server for each tenant
    tenant_id = "user_123"
    
    # Initialize with tenant isolation
    initialize_ripgrep_plugin(
        mode="remote",
        tenant_id=tenant_id,  # Creates /workspace/user_123/
        max_results=25,  # Very conservative for multi-tenant
        timeout_seconds=10,  # Fast timeout
        blocked_patterns=[  # Extra security patterns
            ".git", "node_modules", "__pycache__",
            ".*", "*.env", "*.key", "*.secret",
            "/etc", "/var", "/usr", "/bin", "/root",
            "config", "secrets", "private"
        ]
    )
    
    # All searches are automatically isolated to /workspace/user_123/
    symbols = find_symbol("main", symbol_type="function")
    print(f"Found {symbols['results']['total_found']} main functions for tenant {tenant_id}")


def example_mcp_server_usage():
    """Example: How an MCP server would use this plugin."""
    print("=== MCP Server Usage ===")
    
    class MockMCPServer:
        def __init__(self):
            # Server initialization - configure plugin once at startup
            initialize_ripgrep_plugin(
                mode="remote",
                workspace_root="/mcp/shared-workspace",
                max_results=75,
                timeout_seconds=20,
            )
        
        def handle_search_request(self, pattern: str):
            """Handle incoming search request from MCP client."""
            # Plugin is already configured, just use the tools
            return search_pattern(pattern, max_results=25)
        
        def handle_tenant_request(self, tenant_id: str, query: str):
            """Handle request for specific tenant - requires re-initialization."""
            # Re-initialize for this tenant's context
            initialize_ripgrep_plugin(
                mode="remote",
                tenant_id=tenant_id,
                max_results=50,
            )
            
            # Now search within tenant's isolated workspace
            return search_pattern(query)
    
    # Simulate server usage
    server = MockMCPServer()
    result = server.handle_search_request("import.*requests")
    print(f"MCP search result: {result['results']['total_matches']} matches")


def example_ld_agent_usage():
    """Example: How ld-agent would use this plugin."""
    print("=== ld-agent Usage ===")
    
    # ld-agent would call the init function during plugin loading
    # Configuration could come from environment, config files, or agent settings
    
    # For a local agent
    initialize_ripgrep_plugin(
        mode="local",
        workspace_root=str(Path.cwd()),  # Current working directory
        max_results=200,  # Higher limits for local agent
    )
    
    # Agent can now use tools directly
    context = get_file_context("README.md", line_number=1, context_lines=5)
    if context['error'] is None:
        print(f"File context retrieved: {context['result']['file']}")
    else:
        print(f"Error: {context['error']}")


def example_security_boundaries():
    """Example: Demonstrating security boundary enforcement."""
    print("=== Security Boundaries Demo ===")
    
    # Initialize with restricted paths
    initialize_ripgrep_plugin(
        mode="remote",
        allowed_paths=["/workspace/safe-area"],
        blocked_patterns=["secrets", "*.key", ".env"],
    )
    
    try:
        # This should work - within allowed path
        results = search_files(name_pattern="*.py", paths=["/workspace/safe-area/src"])
        print(f"Allowed search succeeded: {results['results']['total_files']} files")
    except PermissionError as e:
        print(f"Expected security error: {e}")
    
    try:
        # This should fail - outside allowed path
        results = search_files(name_pattern="*.py", paths=["/etc"])
        print("This shouldn't print - security should block it")
    except PermissionError as e:
        print(f"Security correctly blocked: {e}")


def example_configuration_flexibility():
    """Example: Showing configuration flexibility."""
    print("=== Configuration Flexibility ===")
    
    # Development environment - permissive
    initialize_ripgrep_plugin(
        mode="local",
        workspace_root="/Users/dev/project",
        max_results=500,
        max_filesize="100M",
        timeout_seconds=120,
        blocked_patterns=[".git", "node_modules"],  # Minimal blocking
    )
    
    # Production environment - restrictive
    # initialize_ripgrep_plugin(
    #     mode="remote",
    #     allowed_paths=["/app/workspace"],
    #     max_results=25,
    #     max_filesize="1M",
    #     timeout_seconds=5,
    #     blocked_patterns=[
    #         ".git", "node_modules", "__pycache__",
    #         ".*", "*.env", "*.key", "*.secret", "*.pem",
    #         "config", "secrets", "private", "internal"
    #     ]
    # )
    
    print("Plugin configured for development environment")


if __name__ == "__main__":
    """Run examples to demonstrate the plugin usage patterns."""
    
    try:
        print("Ripgrep Plugin Configuration Examples")
        print("=" * 50)
        
        # Run examples (commented out to avoid actual execution)
        # example_local_development()
        # example_local_auto_workspace()
        # example_remote_single_tenant()
        # example_remote_multi_tenant()
        # example_mcp_server_usage()
        # example_ld_agent_usage()
        # example_security_boundaries()
        example_configuration_flexibility()
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"Example execution failed: {e}")


# Additional helper functions for integration

def create_local_config(workspace_path: str = None) -> dict:
    """Create a standard local development configuration."""
    return {
        "mode": "local",
        "workspace_root": workspace_path or str(Path.cwd()),
        "max_results": 200,
        "max_filesize": "50M",
        "timeout_seconds": 60,
        "blocked_patterns": [".git", "node_modules", "__pycache__", ".pytest_cache"]
    }


def create_remote_config(tenant_id: str = None, workspace_root: str = None) -> dict:
    """Create a standard remote deployment configuration."""
    config = {
        "mode": "remote",
        "max_results": 50,
        "max_filesize": "5M",
        "timeout_seconds": 15,
        "blocked_patterns": [
            ".git", "node_modules", "__pycache__",
            ".*", "*.env", "*.key", "*.secret", "*.pem",
            "/etc", "/var", "/usr", "/bin", "/sbin", "/root"
        ]
    }
    
    if tenant_id:
        config["tenant_id"] = tenant_id
    elif workspace_root:
        config["workspace_root"] = workspace_root
    else:
        raise ValueError("Remote config requires either tenant_id or workspace_root")
    
    return config


def initialize_from_config(config: dict):
    """Initialize plugin from configuration dictionary."""
    initialize_ripgrep_plugin(**config) 