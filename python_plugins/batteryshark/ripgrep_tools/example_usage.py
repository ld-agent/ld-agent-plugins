#!/usr/bin/env python3
"""
Example usage of the ripgrep plugin for ld-agent.

This script demonstrates how to use all the available tools in the ripgrep plugin.
"""

import asyncio
import json
from typing import Dict, Any

# Import the plugin tools
from . import (
    search_pattern,
    find_symbol, 
    search_files,
    get_file_context,
    analyze_codebase
)


def pretty_print_result(result: Dict[str, Any], title: str) -> None:
    """Pretty print a result with a title."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2))


async def main():
    """Demonstrate all ripgrep plugin tools."""
    print("🚀 Ripgrep Plugin for ld-agent - Example Usage")
    print("This script demonstrates all available tools in the plugin.")
    
    # 1. Search for Python function definitions
    print("\n1. Searching for Python function definitions...")
    result = search_pattern(
        pattern=r"def\s+\w+\s*\(",
        paths=["."],
        file_types=["py"],
        context_lines=2,
        max_results=5
    )
    
    if result.get("results") and result["results"]["matches"]:
        print(f"Found {result['results']['total_matches']} function definitions")
        for match in result["results"]["matches"][:3]:  # Show first 3
            print(f"  📄 {match['file']}:{match['line']}: {match['content'].strip()}")
    else:
        print("  No function definitions found")

    # 2. Find specific symbols (classes)
    print("\n2. Finding 'Config' class definitions...")
    result = find_symbol(
        symbol="Config",
        symbol_type="class",
        exact_match=False
    )
    
    if result.get("results") and result["results"]["matches"]:
        print(f"Found {result['results']['total_matches']} Config class(es)")
        for match in result["results"]["matches"]:
            print(f"  📄 {match['file']}:{match['line']}: {match['definition'].strip()}")
    else:
        print("  No Config classes found")

    # 3. Search for Python files
    print("\n3. Finding Python files...")
    result = search_files(
        name_pattern="*.py",
        include_stats=True
    )
    
    if result.get("results") and result["results"]["files"]:
        print(f"Found {result['results']['total_files']} Python files")
        for file in result["results"]["files"][:5]:  # Show first 5
            size_kb = (file.get("size", 0) or 0) / 1024
            print(f"  📄 {file['path']} ({size_kb:.1f} KB)")
    else:
        print("  No Python files found")

    # 4. Search for files containing 'async def'
    print("\n4. Finding files containing 'async def'...")
    result = search_files(
        content_pattern="async def",
        include_stats=True
    )
    
    if result.get("results") and result["results"]["files"]:
        print(f"Found {result['results']['total_files']} files with async functions")
        for file in result["results"]["files"][:3]:  # Show first 3
            print(f"  📄 {file['path']} ({file.get('match_count', 0)} matches)")
    else:
        print("  No files with async functions found")

    # 5. Get context from a specific file (if available)
    if result.get("results") and result["results"]["files"]:
        first_file = result["results"]["files"][0]["path"]
        print(f"\n5. Getting context from line 10 in {first_file}...")
        
        context_result = get_file_context(
            file_path=first_file,
            line_number=10,
            context_lines=3,
            include_line_numbers=True
        )
        
        if context_result.get("result"):
            ctx = context_result["result"]
            print(f"  📄 {ctx['file']}:{ctx['target_line']}")
            print(f"  Context ({ctx['total_context_lines']} lines):")
            
            for line in ctx.get("before_context", []):
                print(f"    {line}")
            print(f"  > {ctx['content']}")
            for line in ctx.get("after_context", []):
                print(f"    {line}")
        else:
            print(f"  Could not get context: {context_result.get('error', 'Unknown error')}")

    # 6. Analyze the current codebase
    print("\n6. Analyzing codebase structure...")
    result = analyze_codebase(
        paths=["."],
        include_metrics=True,
        include_language_stats=True,
        max_files_to_scan=100  # Limit for example
    )
    
    if result.get("results"):
        stats = result["results"]
        summary = stats.get("summary", {})
        
        print(f"  📊 Total files: {summary.get('total_files', 0)}")
        print(f"  📊 Total size: {summary.get('total_size_mb', 0):.1f} MB")
        
        if summary.get("total_lines"):
            print(f"  📊 Total lines: {summary['total_lines']:,}")
        
        print("  📊 File types:")
        file_types = stats.get("file_types", {})
        for ext, count in sorted(file_types.items())[:5]:  # Top 5
            print(f"    .{ext}: {count} files")
        
        if stats.get("language_stats"):
            print("  📊 Languages:")
            for lang, info in stats["language_stats"].items():
                print(f"    {lang}: {info['files']} files")

    print("\n✅ Example completed!")
    print("\nℹ️  This plugin provides powerful code search capabilities for AI agents.")
    print("   Configure with environment variables like RIPGREP_MAX_RESULTS, etc.")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 