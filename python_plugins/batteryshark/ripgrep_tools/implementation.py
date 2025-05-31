"""
Implementation module for ripgrep plugin.

This module contains the actual business logic for ripgrep-based code search tools.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Try to import ripgrepy, fall back to CLI-only mode if not available
try:
    from ripgrepy import Ripgrepy, RipGrepNotFound
    HAS_RIPGREPY = True
except ImportError:
    HAS_RIPGREPY = False
    logging.warning("ripgrepy not available, falling back to CLI-only mode")


class Config:
    """Configuration for ripgrep operations based on environment variables."""
    
    def __init__(self):
        self.ripgrep_path = os.getenv("RIPGREP_PATH", "rg")
        self.max_results = int(os.getenv("RIPGREP_MAX_RESULTS", "100"))
        self.max_filesize = os.getenv("RIPGREP_MAX_FILESIZE", "10M")
        self.timeout_seconds = int(os.getenv("RIPGREP_TIMEOUT", "30"))
        
        # Parse allowed paths
        allowed_paths_str = os.getenv("RIPGREP_ALLOWED_PATHS", "")
        self.allowed_paths = [p.strip() for p in allowed_paths_str.split(",") if p.strip()] if allowed_paths_str else None
        
        # Parse blocked patterns
        blocked_patterns_str = os.getenv("RIPGREP_BLOCKED_PATTERNS", ".git,node_modules,__pycache__,.pytest_cache")
        self.blocked_patterns = [p.strip() for p in blocked_patterns_str.split(",") if p.strip()]
        
        self.default_file_types = ["py", "js", "ts", "jsx", "tsx", "java", "c", "cpp", "h", "hpp", "cs", "go", "rs", "rb", "php", "md"]

    def is_path_allowed(self, path: Union[str, Path]) -> bool:
        """Check if a path is allowed based on configuration."""
        if not self.allowed_paths:
            return True
            
        path = Path(path).resolve()
        
        for allowed_path in self.allowed_paths:
            try:
                allowed_path = Path(allowed_path).resolve()
                # Check if path is within allowed directory
                path.relative_to(allowed_path)
                return True
            except (ValueError, OSError):
                continue
                
        return False
    
    def is_pattern_blocked(self, path: Union[str, Path]) -> bool:
        """Check if a path contains blocked patterns."""
        path_str = str(path)
        return any(pattern in path_str for pattern in self.blocked_patterns)


def _verify_ripgrep() -> None:
    """Verify that ripgrep is available."""
    config = Config()
    try:
        result = subprocess.run(
            [config.ripgrep_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise RuntimeError(f"ripgrep not working at {config.ripgrep_path}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        raise RuntimeError(f"ripgrep not found at {config.ripgrep_path}")


def _build_symbol_pattern(symbol: str, symbol_type: str, exact_match: bool) -> str:
    """Build a regex pattern for finding symbols."""
    if exact_match:
        symbol_pattern = re.escape(symbol)
    else:
        symbol_pattern = symbol
        
    if symbol_type.lower() == "function":
        # Match function definitions in various languages
        patterns = [
            rf"def\s+{symbol_pattern}\s*\(",  # Python
            rf"function\s+{symbol_pattern}\s*\(",  # JavaScript
            rf"{symbol_pattern}\s*\([^)]*\)\s*{{",  # C/Java/etc
            rf"fn\s+{symbol_pattern}\s*\(",  # Rust
        ]
        return "|".join(patterns)
    elif symbol_type.lower() == "class":
        patterns = [
            rf"class\s+{symbol_pattern}",  # Python/Java/C#
            rf"struct\s+{symbol_pattern}",  # C/C++/Rust
            rf"interface\s+{symbol_pattern}",  # TypeScript/Java
        ]
        return "|".join(patterns)
    elif symbol_type.lower() == "variable":
        patterns = [
            rf"let\s+{symbol_pattern}\s*=",  # JavaScript/TypeScript
            rf"var\s+{symbol_pattern}\s*=",  # JavaScript
            rf"const\s+{symbol_pattern}\s*=",  # JavaScript/TypeScript
            rf"{symbol_pattern}\s*=",  # General assignment
        ]
        return "|".join(patterns)
    else:
        # ANY or other types - just search for the symbol
        return symbol_pattern


async def _run_ripgrep_command(cmd: List[str]) -> str:
    """Run a ripgrep command asynchronously."""
    config = Config()
    
    def _run():
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout_seconds,
        )
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run)
    
    if result.returncode != 0 and result.stderr:
        logging.warning(f"ripgrep warning: {result.stderr}")
    
    return result.stdout


def _parse_ripgrep_json_output(output: str) -> List[Dict[str, Any]]:
    """Parse ripgrep JSON output into match objects."""
    matches = []
    
    for line in output.strip().split('\n'):
        if not line:
            continue
            
        try:
            data = json.loads(line)
            if data.get('type') == 'match':
                match_data = data.get('data', {})
                
                file_path = match_data.get('path', {}).get('text', '')
                line_number = match_data.get('line_number', 0)
                content = match_data.get('lines', {}).get('text', '').rstrip('\n')
                
                # Extract byte offset if available
                byte_offset = match_data.get('absolute_offset')
                
                # Extract column from submatches if available
                column = None
                submatches = match_data.get('submatches', [])
                if submatches:
                    column = submatches[0].get('start')
                
                match = {
                    "file": file_path,
                    "line": line_number,
                    "column": column,
                    "content": content,
                    "before_context": [],
                    "after_context": [],
                    "byte_offset": byte_offset,
                }
                matches.append(match)
                
        except json.JSONDecodeError:
            # Skip malformed JSON lines
            continue
            
    return matches


async def search_pattern_impl(
    pattern: str,
    paths: Optional[List[str]] = None,
    file_types: Optional[List[str]] = None,
    context_lines: int = 3,
    case_sensitive: bool = False,
    whole_words: bool = False,
    max_results: Optional[int] = None,
) -> Dict[str, Any]:
    """Implementation of pattern search functionality."""
    if not pattern:
        return {
            "query": {"pattern": pattern, "paths": paths, "options": {}},
            "results": {"total_matches": 0, "files_searched": 0, "files_with_matches": 0, "matches": []},
            "error": "Pattern cannot be empty"
        }
    
    config = Config()
    start_time = time.time()
    paths = paths or ["."]
    
    # Validate paths
    for path in paths:
        if not config.is_path_allowed(path):
            return {
                "query": {"pattern": pattern, "paths": paths},
                "results": {"total_matches": 0, "files_searched": 0, "files_with_matches": 0, "matches": []},
                "error": f"Path not allowed: {path}"
            }
    
    try:
        _verify_ripgrep()
        
        # Build ripgrep command
        cmd = [config.ripgrep_path, "--json", "--line-number", "--with-filename"]
        
        if case_sensitive:
            cmd.append("--case-sensitive")
        else:
            cmd.append("--smart-case")
        
        if whole_words:
            cmd.append("--word-regexp")
        
        if context_lines > 0:
            cmd.extend(["--context", str(context_lines)])
        
        if file_types:
            for file_type in file_types:
                cmd.extend(["--type", file_type])
        
        if max_results or config.max_results:
            limit = max_results or config.max_results
            cmd.extend(["--max-count", str(limit)])
        
        cmd.extend(["--max-filesize", config.max_filesize])
        
        # Add blocked patterns as globs
        for blocked_pattern in config.blocked_patterns:
            cmd.extend(["--glob", f"!{blocked_pattern}"])
        
        cmd.append(pattern)
        cmd.extend(paths)
        
        # Run search
        output = await _run_ripgrep_command(cmd)
        matches = _parse_ripgrep_json_output(output)
        
        # Calculate statistics
        files_with_matches = len(set(match["file"] for match in matches))
        search_time = (time.time() - start_time) * 1000
        
        return {
            "query": {
                "pattern": pattern,
                "paths": paths,
                "options": {
                    "case_sensitive": case_sensitive,
                    "whole_words": whole_words,
                    "context_lines": context_lines,
                    "file_types": file_types,
                }
            },
            "results": {
                "total_matches": len(matches),
                "files_searched": 0,  # ripgrep doesn't provide this easily
                "files_with_matches": files_with_matches,
                "search_time_ms": search_time,
                "truncated": max_results and len(matches) >= max_results,
                "matches": matches,
            },
            "error": None,
        }
        
    except Exception as e:
        return {
            "query": {"pattern": pattern, "paths": paths},
            "results": {"total_matches": 0, "files_searched": 0, "files_with_matches": 0, "matches": []},
            "error": str(e)
        }


async def find_symbol_impl(
    symbol: str,
    symbol_type: str = "any",
    paths: Optional[List[str]] = None,
    exact_match: bool = False,
) -> Dict[str, Any]:
    """Implementation of symbol finding functionality."""
    if not symbol:
        return {
            "query": {"symbol": symbol, "symbol_type": symbol_type, "paths": paths, "exact_match": exact_match},
            "results": {"total_matches": 0, "matches": []}
        }
    
    # Build pattern based on symbol type
    pattern = _build_symbol_pattern(symbol, symbol_type, exact_match)
    
    # Use the pattern search with appropriate file types
    config = Config()
    result = await search_pattern_impl(
        pattern=pattern,
        paths=paths,
        file_types=config.default_file_types,
        context_lines=2,
    )
    
    # Convert to symbol match format
    symbol_matches = []
    if result.get("results") and result["results"].get("matches"):
        for match in result["results"]["matches"]:
            symbol_match = {
                "symbol_name": symbol,
                "symbol_type": symbol_type,
                "file": match["file"],
                "line": match["line"],
                "column": match.get("column"),
                "definition": match["content"],
                "context": match.get("before_context", []) + match.get("after_context", []),
                "scope": None,  # Could be enhanced to detect scope
            }
            symbol_matches.append(symbol_match)
    
    return {
        "query": {
            "symbol": symbol,
            "symbol_type": symbol_type,
            "paths": paths,
            "exact_match": exact_match,
        },
        "results": {
            "total_matches": len(symbol_matches),
            "matches": symbol_matches,
        },
    }


async def search_files_impl(
    name_pattern: Optional[str] = None,
    content_pattern: Optional[str] = None,
    paths: Optional[List[str]] = None,
    max_size: Optional[str] = None,
    include_stats: bool = True,
) -> Dict[str, Any]:
    """Implementation of file search functionality."""
    config = Config()
    paths = paths or ["."]
    
    # Validate paths
    for path in paths:
        if not config.is_path_allowed(path):
            return {
                "query": {"name_pattern": name_pattern, "content_pattern": content_pattern, "paths": paths},
                "results": {"total_files": 0, "files": []},
                "error": f"Path not allowed: {path}"
            }
    
    try:
        _verify_ripgrep()
        files = []
        
        if content_pattern:
            # Search for files containing specific content
            result = await search_pattern_impl(
                pattern=content_pattern,
                paths=paths,
                file_types=config.default_file_types if not name_pattern else None,
            )
            
            # Group by file and count matches
            file_matches = {}
            if result.get("results") and result["results"].get("matches"):
                for match in result["results"]["matches"]:
                    file_path = match["file"]
                    if file_path not in file_matches:
                        file_matches[file_path] = 0
                    file_matches[file_path] += 1
            
            for file_path, match_count in file_matches.items():
                if config.is_pattern_blocked(file_path):
                    continue
                
                try:
                    stat = os.stat(file_path)
                    file_info = {
                        "path": file_path,
                        "size": stat.st_size if include_stats else None,
                        "match_count": match_count,
                        "file_type": Path(file_path).suffix[1:] if Path(file_path).suffix else None,
                    }
                    files.append(file_info)
                except OSError:
                    continue
        else:
            # Find files by name pattern
            cmd = [config.ripgrep_path, "--files"]
            
            if name_pattern:
                cmd.extend(["--glob", name_pattern])
            
            if max_size:
                cmd.extend(["--max-filesize", max_size])
            elif config.max_filesize:
                cmd.extend(["--max-filesize", config.max_filesize])
            
            # Add blocked patterns
            for blocked_pattern in config.blocked_patterns:
                cmd.extend(["--glob", f"!{blocked_pattern}"])
            
            cmd.extend(paths)
            
            output = await _run_ripgrep_command(cmd)
            
            for line in output.strip().split('\n'):
                if not line:
                    continue
                
                file_path = line.strip()
                if config.is_pattern_blocked(file_path):
                    continue
                
                try:
                    stat = os.stat(file_path)
                    file_info = {
                        "path": file_path,
                        "size": stat.st_size if include_stats else None,
                        "file_type": Path(file_path).suffix[1:] if Path(file_path).suffix else None,
                        "line_count": None,
                        "match_count": None,
                    }
                    files.append(file_info)
                except OSError:
                    continue
        
        return {
            "query": {
                "name_pattern": name_pattern,
                "content_pattern": content_pattern,
                "paths": paths,
                "max_size": max_size,
            },
            "results": {
                "total_files": len(files),
                "files": files,
            },
        }
        
    except Exception as e:
        return {
            "query": {"name_pattern": name_pattern, "content_pattern": content_pattern, "paths": paths},
            "results": {"total_files": 0, "files": []},
            "error": str(e)
        }


async def get_file_context_impl(
    file_path: str,
    line_number: int,
    context_lines: int = 10,
    include_line_numbers: bool = True,
) -> Dict[str, Any]:
    """Implementation of file context functionality."""
    config = Config()
    
    if not config.is_path_allowed(file_path):
        return {
            "query": {"file_path": file_path, "line_number": line_number, "context_lines": context_lines},
            "error": "File path not allowed"
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        if line_number < 1 or line_number > total_lines:
            return {
                "query": {"file_path": file_path, "line_number": line_number, "context_lines": context_lines},
                "error": f"Line number {line_number} is out of range (file has {total_lines} lines)"
            }
        
        # Calculate context boundaries
        start_line = max(1, line_number - context_lines)
        end_line = min(total_lines, line_number + context_lines)
        
        # Extract context
        target_line = lines[line_number - 1].rstrip('\n')
        before_context = []
        after_context = []
        
        for i in range(start_line - 1, line_number - 1):
            line_content = lines[i].rstrip('\n')
            if include_line_numbers:
                before_context.append(f"{i + 1}: {line_content}")
            else:
                before_context.append(line_content)
        
        for i in range(line_number, end_line):
            line_content = lines[i].rstrip('\n')
            if include_line_numbers:
                after_context.append(f"{i + 1}: {line_content}")
            else:
                after_context.append(line_content)
        
        return {
            "query": {
                "file_path": file_path,
                "line_number": line_number,
                "context_lines": context_lines,
            },
            "result": {
                "file": file_path,
                "target_line": line_number,
                "content": f"{line_number}: {target_line}" if include_line_numbers else target_line,
                "before_context": before_context,
                "after_context": after_context,
                "total_context_lines": len(before_context) + len(after_context) + 1,
                "file_total_lines": total_lines,
            },
        }
        
    except (OSError, UnicodeDecodeError) as e:
        return {
            "query": {"file_path": file_path, "line_number": line_number, "context_lines": context_lines},
            "error": f"Could not read file: {str(e)}"
        }


async def analyze_codebase_impl(
    paths: Optional[List[str]] = None,
    include_metrics: bool = True,
    file_types: Optional[List[str]] = None,
    include_language_stats: bool = True,
    max_files_to_scan: int = 1000,
) -> Dict[str, Any]:
    """Implementation of codebase analysis functionality."""
    config = Config()
    paths = paths or ["."]
    
    # Validate paths
    for path in paths:
        if not config.is_path_allowed(path):
            return {
                "query": {"paths": paths, "include_metrics": include_metrics},
                "results": {},
                "error": f"Path not allowed: {path}"
            }
    
    try:
        # Find all files
        file_result = await search_files_impl(paths=paths, include_stats=True)
        
        if file_result.get("error"):
            return file_result
        
        all_files = file_result["results"]["files"]
        
        # Calculate basic statistics
        total_files = len(all_files)
        total_size = sum(f.get("size", 0) or 0 for f in all_files)
        
        # Count by file type
        file_types_count = {}
        for file_info in all_files:
            ext = file_info.get("file_type") or "no_extension"
            file_types_count[ext] = file_types_count.get(ext, 0) + 1
        
        # Find largest files
        largest_files = sorted(
            [f for f in all_files if f.get("size")],
            key=lambda f: f["size"],
            reverse=True
        )[:10]
        
        # Format largest files
        largest_files_formatted = []
        for file_info in largest_files:
            largest_files_formatted.append({
                "path": file_info["path"],
                "size": file_info["size"],
                "size_mb": round(file_info["size"] / (1024 * 1024), 2),
                "file_type": file_info.get("file_type"),
            })
        
        # Estimate total lines if requested
        total_lines = 0
        if include_metrics and all_files:
            sample_files = all_files[:min(max_files_to_scan, len(all_files))]
            for file_info in sample_files:
                try:
                    with open(file_info["path"], 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                        total_lines += lines
                except (OSError, UnicodeDecodeError):
                    continue
        
        # Language stats (simplified)
        language_stats = {}
        if include_language_stats:
            language_map = {
                "py": "Python", "js": "JavaScript", "ts": "TypeScript",
                "java": "Java", "c": "C", "cpp": "C++", "h": "C/C++",
                "cs": "C#", "go": "Go", "rs": "Rust", "rb": "Ruby",
                "php": "PHP", "md": "Markdown", "html": "HTML",
                "css": "CSS", "json": "JSON", "xml": "XML", "yml": "YAML", "yaml": "YAML"
            }
            
            for ext, count in file_types_count.items():
                if ext in language_map:
                    lang = language_map[ext]
                    if lang not in language_stats:
                        language_stats[lang] = {"files": 0, "extensions": []}
                    language_stats[lang]["files"] += count
                    if ext not in language_stats[lang]["extensions"]:
                        language_stats[lang]["extensions"].append(ext)
        
        return {
            "query": {
                "paths": paths,
                "include_metrics": include_metrics,
                "file_types": file_types,
            },
            "results": {
                "summary": {
                    "total_files": total_files,
                    "total_lines": total_lines if include_metrics else None,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                },
                "file_types": file_types_count,
                "largest_files": largest_files_formatted,
                "language_stats": language_stats if include_language_stats else {},
            },
        }
        
    except Exception as e:
        return {
            "query": {"paths": paths, "include_metrics": include_metrics},
            "results": {},
            "error": str(e)
        } 