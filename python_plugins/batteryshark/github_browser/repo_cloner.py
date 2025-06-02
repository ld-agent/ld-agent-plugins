#!/usr/bin/env python3
"""
Repository Cloner - Local git cloning for bulk operations

This module provides local git cloning capabilities to complement the API-based
GitHub browser. Especially useful for code review automation and bulk file operations
where API rate limits become a concern.

Key capabilities:
- Temporary repository cloning with automatic cleanup
- Hybrid fallback to API if cloning fails
- Efficient bulk file operations on local clones
- Smart caching with configurable TTL
"""

import os
import shutil
import tempfile
import subprocess
import time
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class CloneInfo:
    """Information about a cloned repository"""
    repo_name: str
    org: Optional[str]
    branch: str
    clone_path: str
    clone_time: datetime
    clone_url: str
    full_name: str
    with_submodules: bool = False

class RepositoryCloner:
    """
    Manages local git clones for efficient bulk operations.
    
    Designed to complement the API-based GitHubExplorer for cases where
    local file access is more efficient than repeated API calls.
    """
    
    def __init__(self, 
                 base_temp_dir: Optional[str] = None,
                 auto_cleanup_hours: int = 24,
                 max_clone_size_mb: int = 500):
        """
        Initialize repository cloner.
        
        Args:
            base_temp_dir: Base directory for clones (uses system temp if None)
            auto_cleanup_hours: Hours after which to auto-cleanup old clones
            max_clone_size_mb: Maximum repository size to clone (safety limit)
        """
        self.base_temp_dir = base_temp_dir or tempfile.gettempdir()
        self.auto_cleanup_hours = auto_cleanup_hours
        self.max_clone_size_mb = max_clone_size_mb
        self.active_clones: Dict[str, CloneInfo] = {}
        
        # Create base directory for GitHub clones
        self.github_temp_dir = os.path.join(self.base_temp_dir, "github_browser_clones")
        os.makedirs(self.github_temp_dir, exist_ok=True)
        
        # Auto-cleanup old clones on startup
        self._cleanup_old_clones()
    
    def clone_repository(self,
                        repo_name: str,
                        org: Optional[str] = None,
                        branch: Optional[str] = None,
                        auth_token: Optional[str] = None,
                        depth: Optional[int] = 1,
                        recurse_submodules: bool = False,
                        force_reclone: bool = False) -> Optional[CloneInfo]:
        """
        Clone a repository to local temporary directory.
        
        Args:
            repo_name: Repository name
            org: Organization/user name
            branch: Branch to clone (defaults to default branch)
            auth_token: GitHub token for private repos
            depth: Clone depth (1 for shallow clone, None for full)
            recurse_submodules: Whether to recursively clone submodules
            force_reclone: Force re-clone even if already exists
            
        Returns:
            CloneInfo object with clone details, or None if failed
        """
        try:
            full_name = f"{org}/{repo_name}" if org else repo_name
            clone_key = f"{full_name}#{branch or 'default'}{'#submodules' if recurse_submodules else ''}"
            
            # Check if already cloned and not forcing re-clone
            if not force_reclone and clone_key in self.active_clones:
                clone_info = self.active_clones[clone_key]
                if os.path.exists(clone_info.clone_path):
                    submodule_msg = " (with submodules)" if recurse_submodules else ""
                    print(f"📂 Using existing clone{submodule_msg}: {clone_info.clone_path}")
                    return clone_info
                else:
                    # Path doesn't exist, remove from cache
                    del self.active_clones[clone_key]
            
            # Construct clone URL
            if auth_token:
                clone_url = f"https://{auth_token}@github.com/{full_name}.git"
            else:
                clone_url = f"https://github.com/{full_name}.git"
            
            # Create unique clone directory
            timestamp = int(time.time())
            safe_name = full_name.replace("/", "_").replace(".", "_")
            submodule_suffix = "_submodules" if recurse_submodules else ""
            clone_dir_name = f"{safe_name}{submodule_suffix}_{timestamp}"
            clone_path = os.path.join(self.github_temp_dir, clone_dir_name)
            
            submodule_msg = " with submodules" if recurse_submodules else ""
            print(f"🔄 Cloning {full_name}{submodule_msg} to {clone_path}...")
            
            # Build git clone command
            cmd = ["git", "clone"]
            
            if depth:
                cmd.extend(["--depth", str(depth)])
            
            if branch:
                cmd.extend(["--branch", branch])
            
            if recurse_submodules:
                cmd.extend(["--recurse-submodules"])
                # If using shallow clone with submodules, also shallow clone submodules
                if depth:
                    cmd.extend(["--shallow-submodules"])
            
            cmd.extend([clone_url, clone_path])
            
            # Execute clone with timeout (longer for submodules)
            timeout = 600 if recurse_submodules else 300  # 10 minutes for submodules, 5 for regular
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                print(f"❌ Clone failed: {result.stderr}")
                return None
            
            # If we cloned with submodules, update and initialize them properly
            if recurse_submodules and os.path.exists(clone_path):
                try:
                    # Ensure submodules are properly initialized and updated
                    submodule_init_cmd = ["git", "submodule", "update", "--init", "--recursive"]
                    if depth:
                        submodule_init_cmd.extend(["--depth", str(depth)])
                    
                    subprocess.run(
                        submodule_init_cmd,
                        cwd=clone_path,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes for submodule update
                    )
                except subprocess.TimeoutExpired:
                    print("⚠️  Submodule update timed out, but main repository was cloned successfully")
                except Exception as e:
                    print(f"⚠️  Submodule initialization warning: {e}")
            
            # Check clone size (safety check)
            clone_size_mb = self._get_directory_size_mb(clone_path)
            if clone_size_mb > self.max_clone_size_mb:
                print(f"⚠️  Clone size ({clone_size_mb}MB) exceeds limit ({self.max_clone_size_mb}MB)")
                shutil.rmtree(clone_path, ignore_errors=True)
                return None
            
            # Create clone info
            clone_info = CloneInfo(
                repo_name=repo_name,
                org=org,
                branch=branch or self._get_default_branch(clone_path),
                clone_path=clone_path,
                clone_time=datetime.now(),
                clone_url=clone_url,
                full_name=full_name,
                with_submodules=recurse_submodules
            )
            
            self.active_clones[clone_key] = clone_info
            
            submodule_msg = " with submodules" if recurse_submodules else ""
            print(f"✅ Successfully cloned {full_name}{submodule_msg} ({clone_size_mb}MB)")
            return clone_info
            
        except subprocess.TimeoutExpired:
            timeout_type = "with submodules" if recurse_submodules else ""
            print(f"❌ Clone timeout for {full_name} {timeout_type}")
            return None
        except Exception as e:
            print(f"❌ Clone error for {full_name}: {e}")
            return None
    
    def get_files_from_clone(self,
                           clone_info: CloneInfo,
                           file_patterns: List[str],
                           include_content: bool = True) -> List[Dict[str, Any]]:
        """
        Get files from local clone using glob patterns.
        
        Args:
            clone_info: Clone information
            file_patterns: List of glob patterns
            include_content: Whether to include file content
            
        Returns:
            List of file information dictionaries
        """
        try:
            import fnmatch
            
            if not os.path.exists(clone_info.clone_path):
                print(f"❌ Clone path no longer exists: {clone_info.clone_path}")
                return []
            
            # Find all files in the clone
            all_files = []
            for root, dirs, files in os.walk(clone_info.clone_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    # Make path relative to clone root
                    rel_path = os.path.relpath(file_path, clone_info.clone_path)
                    all_files.append((rel_path, file_path))
            
            # Filter files by patterns
            matched_files = []
            for pattern in file_patterns:
                for rel_path, abs_path in all_files:
                    if fnmatch.fnmatch(rel_path, pattern):
                        matched_files.append((rel_path, abs_path))
            
            # Remove duplicates while preserving order
            seen = set()
            unique_files = []
            for rel_path, abs_path in matched_files:
                if rel_path not in seen:
                    seen.add(rel_path)
                    unique_files.append((rel_path, abs_path))
            
            # Build file info
            file_results = []
            for rel_path, abs_path in unique_files:
                try:
                    stat = os.stat(abs_path)
                    file_info = {
                        'path': rel_path,
                        'name': os.path.basename(rel_path),
                        'size': stat.st_size,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime),
                        'source': 'local_clone',
                        'clone_path': clone_info.clone_path
                    }
                    
                    if include_content:
                        try:
                            with open(abs_path, 'r', encoding='utf-8') as f:
                                file_info['content'] = f.read()
                        except UnicodeDecodeError:
                            # Binary file
                            file_info['content'] = None
                            file_info['is_binary'] = True
                        except Exception as e:
                            file_info['content'] = None
                            file_info['error'] = str(e)
                    
                    file_results.append(file_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing file {rel_path}: {e}")
                    continue
            
            return file_results
            
        except Exception as e:
            print(f"❌ Error getting files from clone: {e}")
            return []
    
    def cleanup_clone(self, clone_key_or_path: str) -> bool:
        """
        Clean up a specific clone.
        
        Args:
            clone_key_or_path: Clone key or path to clean up
            
        Returns:
            True if successfully cleaned up
        """
        try:
            # Find clone info
            clone_info = None
            if clone_key_or_path in self.active_clones:
                clone_info = self.active_clones[clone_key_or_path]
                del self.active_clones[clone_key_or_path]
            else:
                # Try to find by path
                for key, info in list(self.active_clones.items()):
                    if info.clone_path == clone_key_or_path:
                        clone_info = info
                        del self.active_clones[key]
                        break
            
            # Remove directory
            if clone_info and os.path.exists(clone_info.clone_path):
                shutil.rmtree(clone_info.clone_path, ignore_errors=True)
                print(f"🧹 Cleaned up clone: {clone_info.full_name}")
                return True
            elif os.path.exists(clone_key_or_path):
                shutil.rmtree(clone_key_or_path, ignore_errors=True)
                print(f"🧹 Cleaned up clone directory: {clone_key_or_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error cleaning up clone: {e}")
            return False
    
    def cleanup_all_clones(self) -> int:
        """
        Clean up all active clones.
        
        Returns:
            Number of clones cleaned up
        """
        count = 0
        for key in list(self.active_clones.keys()):
            if self.cleanup_clone(key):
                count += 1
        return count
    
    def _cleanup_old_clones(self):
        """Clean up old clones based on age."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.auto_cleanup_hours)
            
            # Clean up tracked clones
            to_remove = []
            for key, clone_info in self.active_clones.items():
                if clone_info.clone_time < cutoff_time:
                    to_remove.append(key)
            
            for key in to_remove:
                self.cleanup_clone(key)
            
            # Clean up orphaned directories
            if os.path.exists(self.github_temp_dir):
                for item in os.listdir(self.github_temp_dir):
                    item_path = os.path.join(self.github_temp_dir, item)
                    if os.path.isdir(item_path):
                        try:
                            # Check modification time
                            stat = os.stat(item_path)
                            mod_time = datetime.fromtimestamp(stat.st_mtime)
                            if mod_time < cutoff_time:
                                shutil.rmtree(item_path, ignore_errors=True)
                                print(f"🧹 Cleaned up orphaned clone: {item}")
                        except Exception:
                            continue
                            
        except Exception as e:
            logger.warning(f"Error during auto-cleanup: {e}")
    
    def _get_directory_size_mb(self, path: str) -> float:
        """Get directory size in MB."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        continue
        except:
            return 0
        return total_size / (1024 * 1024)
    
    def _get_default_branch(self, clone_path: str) -> str:
        """Get the default branch name from a clone."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=clone_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "main"  # fallback
    
    def get_clone_status(self) -> Dict[str, Any]:
        """Get status of all active clones."""
        return {
            'active_clones': len(self.active_clones),
            'total_size_mb': sum(
                self._get_directory_size_mb(info.clone_path) 
                for info in self.active_clones.values()
                if os.path.exists(info.clone_path)
            ),
            'clones': [
                {
                    'full_name': info.full_name,
                    'branch': info.branch,
                    'clone_time': info.clone_time.isoformat(),
                    'size_mb': self._get_directory_size_mb(info.clone_path)
                }
                for info in self.active_clones.values()
            ]
        }

# Global cloner instance
_repository_cloner = None

def get_repository_cloner() -> RepositoryCloner:
    """Get or create the global repository cloner instance."""
    global _repository_cloner
    if _repository_cloner is None:
        _repository_cloner = RepositoryCloner()
    return _repository_cloner 