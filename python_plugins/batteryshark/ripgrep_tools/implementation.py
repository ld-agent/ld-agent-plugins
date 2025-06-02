"""
Implementation module for the ripgrep plugin.

This module contains the actual implementation of all the plugin functions,
separated from the public API for better organization and testability.
"""

import asyncio
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import ripgrepy

# Global configuration state
_plugin_config = {
    "initialized": False,
    "mode": "local",
    "allowed_paths": [],
    "blocked_patterns": [],
    "max_results": 100,
    "max_filesize": "10M",
    "timeout_seconds": 30,
    "tenant_id": None,
}


def initialize_security_config(
    mode: str,
    allowed_paths: List[str],
    blocked_patterns: List[str],
    max_results: int,
    max_filesize: str,
    timeout_seconds: int,
    tenant_id: Optional[str] = None,
) -> None:
    """Initialize the global security configuration."""
    global _plugin_config
    
    _plugin_config.update({
        "initialized": True,
        "mode": mode,
        "allowed_paths": allowed_paths,
        "blocked_patterns": blocked_patterns,
        "max_results": max_results,
        "max_filesize": max_filesize,
        "timeout_seconds": timeout_seconds,
        "tenant_id": tenant_id,
    })


def _check_initialized() -> None:
    """Check if the plugin has been initialized."""
    if not _plugin_config["initialized"]:
        raise RuntimeError(
            "Plugin has not been initialized. Call initialize_ripgrep_plugin() first."
        )


def _validate_paths(paths: Optional[List[str]]) -> List[str]:
    """Validate that search paths are within allowed boundaries."""
    _check_initialized()
    
    if paths is None:
        # Use configured allowed paths
        return _plugin_config["allowed_paths"]
    
    validated_paths = []
    allowed_paths = [Path(p).resolve() for p in _plugin_config["allowed_paths"]]
    
    for path in paths:
        path_obj = Path(path).resolve()
        
        # Check if path is within any allowed path
        is_allowed = False
        for allowed_path in allowed_paths:
            try:
                path_obj.relative_to(allowed_path)
                is_allowed = True
                break
            except ValueError:
                continue
        
        if not is_allowed:
            raise PermissionError(
                f"Path '{path}' is not within allowed search boundaries. "
                f"Allowed paths: {_plugin_config['allowed_paths']}"
            )
        
        validated_paths.append(str(path_obj))
    
    return validated_paths


def _get_ripgrep_executable() -> str:
    """Get the ripgrep executable path."""
    return os.environ.get("RIPGREP_PATH", "rg")


def _should_block_pattern(pattern: str) -> bool:
    """Check if a pattern should be blocked for security."""
    _check_initialized()
    
    # Block patterns that might access sensitive files
    if _plugin_config["mode"] == "remote":
        dangerous_patterns = [
            r"\.env", r"\.key", r"\.pem", r"password", r"secret",
            r"/etc/", r"/var/", r"/usr/", r"/bin/", r"/sbin/",
            r"id_rsa", r"private", r"token"
        ]
        
        for dangerous in dangerous_patterns:
            if re.search(dangerous, pattern, re.IGNORECASE):
                return True
    
    return False


def _build_ripgrep_command(
    pattern: str,
    paths: List[str],
    file_types: Optional[List[str]] = None,
    context_lines: int = 0,
    case_sensitive: bool = False,
    whole_words: bool = False,
    files_only: bool = False,
    max_count: Optional[int] = None,
) -> List[str]:
    """Build ripgrep command with proper arguments."""
    cmd = [_get_ripgrep_executable()]
    
    # Basic search options
    if not case_sensitive:
        cmd.append("--smart-case")
    
    if whole_words:
        cmd.append("--word-regexp")
    
    if files_only:
        cmd.append("--files-with-matches")
    
    # Context lines
    if context_lines > 0:
        cmd.extend(["-C", str(context_lines)])
    
    # File type filters
    if file_types:
        for file_type in file_types:
            # Remove leading dot if present
            file_type = file_type.lstrip(".")
            cmd.extend(["-t", file_type])
    
    # Output format
    cmd.extend(["--json", "--line-number", "--column"])
    
    # Size limit
    if _plugin_config["max_filesize"]:
        cmd.extend(["--max-filesize", _plugin_config["max_filesize"]])
    
    # Blocked patterns
    for blocked in _plugin_config["blocked_patterns"]:
        cmd.extend(["--glob", f"!{blocked}"])
    
    # Max count
    if max_count:
        cmd.extend(["-m", str(max_count)])
    
    # Pattern and paths
    cmd.append(pattern)
    cmd.extend(paths)
    
    return cmd


async def _run_ripgrep_command(cmd: List[str]) -> Tuple[str, str, int]:
    """Run ripgrep command asynchronously with timeout."""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=_plugin_config["allowed_paths"][0] if _plugin_config["allowed_paths"] else None,
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=_plugin_config["timeout_seconds"]
        )
        
        return stdout.decode(), stderr.decode(), process.returncode
    
    except asyncio.TimeoutError:
        if process:
            process.terminate()
            await process.wait()
        raise RuntimeError(f"Search timed out after {_plugin_config['timeout_seconds']} seconds")
    
    except Exception as e:
        raise RuntimeError(f"Failed to execute ripgrep: {e}")


def _parse_ripgrep_json_output(output: str) -> List[Dict[str, Any]]:
    """Parse ripgrep JSON output into structured results."""
    results = []
    
    for line in output.strip().split('\n'):
        if not line:
            continue
        
        try:
            entry = json.loads(line)
            if entry.get("type") == "match":
                data = entry.get("data", {})
                results.append({
                    "file": data.get("path", {}).get("text", ""),
                    "line": data.get("line_number"),
                    "column": data.get("submatches", [{}])[0].get("start", 0) + 1,
                    "content": data.get("lines", {}).get("text", "").rstrip(),
                    "before_context": [],
                    "after_context": [],
                })
        except json.JSONDecodeError:
            continue
    
    return results


async def search_pattern_impl(
    pattern: str,
    paths: Optional[List[str]] = None,
    file_types: Optional[List[str]] = None,
    context_lines: int = 3,
    case_sensitive: bool = False,
    whole_words: bool = False,
    max_results: Optional[int] = None,
) -> Dict[str, Any]:
    """Implementation for search_pattern function."""
    start_time = time.time()
    
    try:
        # Validate inputs
        if not pattern.strip():
            raise ValueError("Search pattern cannot be empty")
        
        if _should_block_pattern(pattern):
            raise ValueError("Search pattern contains blocked content")
        
        # Validate and resolve paths
        validated_paths = _validate_paths(paths)
        
        # Apply result limits
        effective_max_results = min(
            max_results or _plugin_config["max_results"],
            _plugin_config["max_results"]
        )
        
        # Build and run command
        cmd = _build_ripgrep_command(
            pattern=pattern,
            paths=validated_paths,
            file_types=file_types,
            context_lines=context_lines,
            case_sensitive=case_sensitive,
            whole_words=whole_words,
            max_count=effective_max_results,
        )
        
        stdout, stderr, returncode = await _run_ripgrep_command(cmd)
        
        # Parse results
        matches = _parse_ripgrep_json_output(stdout)
        
        # Limit results
        if len(matches) > effective_max_results:
            matches = matches[:effective_max_results]
        
        return {
            "query": {
                "pattern": pattern,
                "paths": validated_paths,
                "file_types": file_types,
                "context_lines": context_lines,
                "case_sensitive": case_sensitive,
                "whole_words": whole_words,
                "max_results": effective_max_results,
            },
            "results": {
                "total_matches": len(matches),
                "search_time": time.time() - start_time,
                "matches": matches,
            },
            "error": None,
        }
    
    except Exception as e:
        return {
            "query": {
                "pattern": pattern,
                "paths": paths,
                "file_types": file_types,
                "context_lines": context_lines,
                "case_sensitive": case_sensitive,
                "whole_words": whole_words,
            },
            "results": None,
            "error": str(e),
        }


async def find_symbol_impl(
    symbol: str,
    symbol_type: str = "any",
    paths: Optional[List[str]] = None,
    exact_match: bool = False,
) -> Dict[str, Any]:
    """Implementation for find_symbol function."""
    try:
        if not symbol.strip():
            raise ValueError("Symbol name cannot be empty")
        
        # Define symbol patterns
        symbol_patterns = {
            "function": [
                rf"def\s+{symbol}\s*\(",  # Python
                rf"function\s+{symbol}\s*\(",  # JavaScript
                rf"fn\s+{symbol}\s*\(",  # Rust
                rf"{symbol}\s*:\s*function",  # JavaScript object method
            ],
            "class": [
                rf"class\s+{symbol}\s*[:\(]",  # Python, C++
                rf"struct\s+{symbol}\s*\{{",  # C/C++, Rust
                rf"interface\s+{symbol}\s*\{{",  # TypeScript
            ],
            "variable": [
                rf"let\s+{symbol}\s*=",  # JavaScript
                rf"var\s+{symbol}\s*=",  # JavaScript
                rf"const\s+{symbol}\s*=",  # JavaScript
                rf"{symbol}\s*=\s*",  # General assignment
            ],
            "any": [rf"\b{symbol}\b"],  # Any occurrence
        }
        
        if symbol_type not in symbol_patterns:
            symbol_type = "any"
        
        patterns = symbol_patterns[symbol_type]
        
        # Search for each pattern
        all_matches = []
        validated_paths = _validate_paths(paths)
        
        for pattern in patterns:
            cmd = _build_ripgrep_command(
                pattern=pattern,
                paths=validated_paths,
                case_sensitive=exact_match,
                max_count=_plugin_config["max_results"],
            )
            
            stdout, stderr, returncode = await _run_ripgrep_command(cmd)
            matches = _parse_ripgrep_json_output(stdout)
            
            for match in matches:
                match.update({
                    "symbol_name": symbol,
                    "symbol_type": symbol_type,
                    "definition": match["content"],
                    "scope": "unknown",
                })
            
            all_matches.extend(matches)
        
        # Remove duplicates based on file and line
        seen = set()
        unique_matches = []
        for match in all_matches:
            key = (match["file"], match["line"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return {
            "query": {
                "symbol": symbol,
                "symbol_type": symbol_type,
                "paths": validated_paths,
                "exact_match": exact_match,
            },
            "results": {
                "total_found": len(unique_matches),
                "symbols": unique_matches,
            },
            "error": None,
        }
    
    except Exception as e:
        return {
            "query": {
                "symbol": symbol,
                "symbol_type": symbol_type,
                "paths": paths,
                "exact_match": exact_match,
            },
            "results": None,
            "error": str(e),
        }


async def search_files_impl(
    name_pattern: Optional[str] = None,
    content_pattern: Optional[str] = None,
    paths: Optional[List[str]] = None,
    max_size: Optional[str] = None,
    include_stats: bool = True,
) -> Dict[str, Any]:
    """Implementation for search_files function."""
    try:
        if not name_pattern and not content_pattern:
            raise ValueError("Either name_pattern or content_pattern must be provided")
        
        validated_paths = _validate_paths(paths)
        results = []
        
        if name_pattern:
            # Use ripgrep's file listing capability
            cmd = [_get_ripgrep_executable(), "--files"]
            
            # Add glob pattern
            cmd.extend(["--glob", name_pattern])
            
            # Size limit
            if max_size or _plugin_config["max_filesize"]:
                size_limit = max_size or _plugin_config["max_filesize"]
                cmd.extend(["--max-filesize", size_limit])
            
            # Blocked patterns
            for blocked in _plugin_config["blocked_patterns"]:
                cmd.extend(["--glob", f"!{blocked}"])
            
            cmd.extend(validated_paths)
            
            stdout, stderr, returncode = await _run_ripgrep_command(cmd)
            
            for line in stdout.strip().split('\n'):
                if line:
                    file_path = line.strip()
                    file_info = {"path": file_path}
                    
                    if include_stats:
                        try:
                            path_obj = Path(file_path)
                            if path_obj.exists():
                                stat = path_obj.stat()
                                file_info.update({
                                    "size": stat.st_size,
                                    "file_type": path_obj.suffix.lstrip('.') or 'no_extension',
                                })
                        except Exception:
                            pass
                    
                    results.append(file_info)
        
        if content_pattern:
            # Search within files
            cmd = _build_ripgrep_command(
                pattern=content_pattern,
                paths=validated_paths,
                files_only=True,
                max_count=_plugin_config["max_results"],
            )
            
            stdout, stderr, returncode = await _run_ripgrep_command(cmd)
            
            for line in stdout.strip().split('\n'):
                if line:
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "match":
                            file_path = entry.get("data", {}).get("path", {}).get("text", "")
                            
                            # Check if already in results
                            existing = next((r for r in results if r["path"] == file_path), None)
                            if not existing:
                                file_info = {"path": file_path}
                                
                                if include_stats:
                                    try:
                                        path_obj = Path(file_path)
                                        if path_obj.exists():
                                            stat = path_obj.stat()
                                            file_info.update({
                                                "size": stat.st_size,
                                                "file_type": path_obj.suffix.lstrip('.') or 'no_extension',
                                            })
                                    except Exception:
                                        pass
                                
                                results.append(file_info)
                    except json.JSONDecodeError:
                        continue
        
        # Limit results
        if len(results) > _plugin_config["max_results"]:
            results = results[:_plugin_config["max_results"]]
        
        return {
            "query": {
                "name_pattern": name_pattern,
                "content_pattern": content_pattern,
                "paths": validated_paths,
                "max_size": max_size,
                "include_stats": include_stats,
            },
            "results": {
                "total_files": len(results),
                "files": results,
            },
            "error": None,
        }
    
    except Exception as e:
        return {
            "query": {
                "name_pattern": name_pattern,
                "content_pattern": content_pattern,
                "paths": paths,
                "max_size": max_size,
                "include_stats": include_stats,
            },
            "results": None,
            "error": str(e),
        }


async def get_file_context_impl(
    file_path: str,
    line_number: int,
    context_lines: int = 10,
    include_line_numbers: bool = True,
) -> Dict[str, Any]:
    """Implementation for get_file_context function."""
    try:
        if line_number < 1:
            raise ValueError("Line number must be >= 1")
        
        # Validate file path
        validated_paths = _validate_paths([file_path])
        actual_file_path = validated_paths[0]
        
        # Read file
        try:
            with open(actual_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {e}")
        
        total_lines = len(lines)
        
        if line_number > total_lines:
            raise ValueError(f"Line number {line_number} exceeds file length ({total_lines} lines)")
        
        # Calculate context range
        start_line = max(1, line_number - context_lines)
        end_line = min(total_lines, line_number + context_lines)
        
        # Extract context
        target_content = lines[line_number - 1].rstrip() if line_number <= total_lines else ""
        
        before_context = []
        for i in range(start_line - 1, line_number - 1):
            line_content = lines[i].rstrip()
            if include_line_numbers:
                before_context.append(f"{i + 1:4d}: {line_content}")
            else:
                before_context.append(line_content)
        
        after_context = []
        for i in range(line_number, min(end_line, total_lines)):
            line_content = lines[i].rstrip()
            if include_line_numbers:
                after_context.append(f"{i + 1:4d}: {line_content}")
            else:
                after_context.append(line_content)
        
        return {
            "query": {
                "file_path": file_path,
                "line_number": line_number,
                "context_lines": context_lines,
                "include_line_numbers": include_line_numbers,
            },
            "result": {
                "file": actual_file_path,
                "target_line": line_number,
                "content": target_content,
                "before_context": before_context,
                "after_context": after_context,
                "total_context_lines": len(before_context) + 1 + len(after_context),
                "file_total_lines": total_lines,
            },
            "error": None,
        }
    
    except Exception as e:
        return {
            "query": {
                "file_path": file_path,
                "line_number": line_number,
                "context_lines": context_lines,
                "include_line_numbers": include_line_numbers,
            },
            "result": None,
            "error": str(e),
        }


async def analyze_codebase_impl(
    paths: Optional[List[str]] = None,
    include_metrics: bool = True,
    file_types: Optional[List[str]] = None,
    include_language_stats: bool = True,
    max_files_to_scan: int = 1000,
) -> Dict[str, Any]:
    """Implementation for analyze_codebase function."""
    try:
        validated_paths = _validate_paths(paths)
        
        # Get file listing
        cmd = [_get_ripgrep_executable(), "--files"]
        
        # Add file type filters
        if file_types:
            for file_type in file_types:
                file_type = file_type.lstrip(".")
                cmd.extend(["-t", file_type])
        
        # Blocked patterns
        for blocked in _plugin_config["blocked_patterns"]:
            cmd.extend(["--glob", f"!{blocked}"])
        
        cmd.extend(validated_paths)
        
        stdout, stderr, returncode = await _run_ripgrep_command(cmd)
        
        all_files = []
        for line in stdout.strip().split('\n'):
            if line:
                all_files.append(line.strip())
        
        # Limit files to scan
        if len(all_files) > max_files_to_scan:
            all_files = all_files[:max_files_to_scan]
        
        # Analyze files
        file_types_count = {}
        language_stats = {}
        total_size = 0
        total_lines = 0
        largest_files = []
        
        for file_path in all_files:
            try:
                path_obj = Path(file_path)
                if not path_obj.exists():
                    continue
                
                stat = path_obj.stat()
                file_size = stat.st_size
                total_size += file_size
                
                file_ext = path_obj.suffix.lstrip('.') or 'no_extension'
                file_types_count[file_ext] = file_types_count.get(file_ext, 0) + 1
                
                # Count lines if metrics enabled
                if include_metrics:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = sum(1 for _ in f)
                        total_lines += line_count
                        
                        largest_files.append({
                            "path": file_path,
                            "size": file_size,
                            "lines": line_count,
                        })
                    except Exception:
                        pass
                
                # Language statistics
                if include_language_stats:
                    language = _detect_language(file_ext)
                    if language not in language_stats:
                        language_stats[language] = {"files": 0, "size": 0, "lines": 0}
                    language_stats[language]["files"] += 1
                    language_stats[language]["size"] += file_size
                    if include_metrics and 'line_count' in locals():
                        language_stats[language]["lines"] += line_count
            
            except Exception:
                continue
        
        # Sort largest files
        largest_files.sort(key=lambda x: x["size"], reverse=True)
        largest_files = largest_files[:10]  # Top 10
        
        return {
            "query": {
                "paths": validated_paths,
                "include_metrics": include_metrics,
                "file_types": file_types,
                "include_language_stats": include_language_stats,
                "max_files_to_scan": max_files_to_scan,
            },
            "results": {
                "summary": {
                    "total_files": len(all_files),
                    "total_size": total_size,
                    "total_lines": total_lines if include_metrics else None,
                },
                "file_types": file_types_count,
                "largest_files": largest_files if include_metrics else [],
                "language_stats": language_stats if include_language_stats else {},
                "directory_breakdown": _analyze_directory_structure(all_files),
            },
            "error": None,
        }
    
    except Exception as e:
        return {
            "query": {
                "paths": paths,
                "include_metrics": include_metrics,
                "file_types": file_types,
                "include_language_stats": include_language_stats,
                "max_files_to_scan": max_files_to_scan,
            },
            "results": None,
            "error": str(e),
        }


def _detect_language(file_ext: str) -> str:
    """Detect programming language from file extension."""
    language_map = {
        'py': 'Python',
        'js': 'JavaScript',
        'ts': 'TypeScript',
        'java': 'Java',
        'cpp': 'C++',
        'c': 'C',
        'h': 'C/C++',
        'rs': 'Rust',
        'go': 'Go',
        'php': 'PHP',
        'rb': 'Ruby',
        'swift': 'Swift',
        'kt': 'Kotlin',
        'cs': 'C#',
        'html': 'HTML',
        'css': 'CSS',
        'scss': 'SCSS',
        'json': 'JSON',
        'xml': 'XML',
        'yaml': 'YAML',
        'yml': 'YAML',
        'md': 'Markdown',
        'sql': 'SQL',
        'sh': 'Shell',
        'bash': 'Shell',
        'ps1': 'PowerShell',
    }
    
    return language_map.get(file_ext.lower(), 'Other')


def _analyze_directory_structure(files: List[str]) -> Dict[str, Any]:
    """Analyze directory structure from file list."""
    directories = {}
    
    for file_path in files:
        path_obj = Path(file_path)
        directory = str(path_obj.parent)
        
        if directory not in directories:
            directories[directory] = {"files": 0, "total_size": 0}
        
        directories[directory]["files"] += 1
        
        try:
            if path_obj.exists():
                directories[directory]["total_size"] += path_obj.stat().st_size
        except Exception:
            pass
    
    return directories 