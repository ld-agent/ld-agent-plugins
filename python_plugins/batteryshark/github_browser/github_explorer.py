#!/usr/bin/env python3
"""
GitHub Explorer - A clean, AI-focused GitHub API client

This module provides a streamlined interface for AI agents to explore and understand
GitHub repositories. It uses PyGithub for the heavy lifting and integrates with
existing GitHub App authentication.

Key capabilities:
- Search for files and content
- Repository exploration and file traversal
- Pull requests, commits, issues, and discussions
- Contributor information
- Clean data structures optimized for AI consumption
"""

import os
import base64
import urllib3
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

from github import Github, GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Issue import Issue
from github.GitCommit import GitCommit
from github.NamedUser import NamedUser

# Disable SSL warnings for internal GitHub Enterprise servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import your existing token function
try:
    from .get_github_app_token import get_github_app_token
except ImportError:
    print("⚠️  GitHub App token function not found. You'll need to provide a token manually.")
    get_github_app_token = None


@dataclass
class FileInfo:
    """Clean file information structure for AI consumption"""
    name: str
    path: str
    size: int
    sha: str
    download_url: Optional[str]
    html_url: str
    type: str  # 'file' or 'dir'
    content: Optional[str] = None  # Base64 decoded content if requested


@dataclass
class RepositoryInfo:
    """Clean repository information structure"""
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    default_branch: str
    language: Optional[str]
    languages: Dict[str, int]  # Language breakdown
    size: int
    stars: int
    forks: int
    open_issues: int
    created_at: datetime
    updated_at: datetime
    clone_url: str
    html_url: str
    topics: List[str]


class GitHubExplorer:
    """
    AI-focused GitHub repository explorer using PyGithub.
    
    Designed specifically for agentic AI systems that need to understand
    and navigate code repositories efficiently.
    """
    
    def __init__(self, 
                 token: Optional[str] = None,
                 base_url: str = "https://api.github.com",
                 org: Optional[str] = None,
                 app_id: Optional[str] = None,
                 private_key_path: Optional[str] = None,
                 verify_ssl: bool = None,
                 auth_preference: Optional[str] = None):
        """
        Initialize GitHub Explorer.
        
        Args:
            token: GitHub token (PAT or App token)
            base_url: GitHub API base URL 
            org: Default organization name
            app_id: GitHub App ID (for app authentication)
            private_key_path: Path to GitHub App private key
            verify_ssl: Whether to verify SSL certificates (auto-detected for internal servers)
            auth_preference: Authentication preference ('app', 'user', 'auto')
        """
        self.base_url = base_url
        self.org = org
        self.auth_method = None  # Track which auth method was used
        
        # Get auth preference from parameter or environment
        auth_pref = auth_preference or os.getenv('GITHUB_AUTH_PREFERENCE', 'auto').lower()
        
        # Auto-detect SSL verification for internal servers
        if verify_ssl is None:
            self.verify_ssl = base_url == "https://api.github.com"
        else:
            self.verify_ssl = verify_ssl
        
        if not self.verify_ssl:
            print("⚠️  SSL verification disabled for internal GitHub Enterprise")
        
        # Enhanced authentication logic based on preference
        if not token:
            token = self._get_preferred_token(auth_pref, app_id, private_key_path)
        
        if not token:
            raise ValueError(
                "GitHub token required. Provide token parameter, set GITHUB_TOKEN/GITHUB_USER_TOKEN env var, "
                "or configure GitHub App authentication."
            )
        
        # Initialize PyGithub with SSL verification setting
        if base_url == "https://api.github.com":
            self.github = Github(token)
        else:
            self.github = Github(base_url=base_url, login_or_token=token, verify=self.verify_ssl)
        
        print(f"✅ GitHub Explorer initialized using {self.auth_method} authentication")
    
    def _get_preferred_token(self, auth_preference: str, app_id: Optional[str], private_key_path: Optional[str]) -> Optional[str]:
        """
        Get authentication token based on preference and availability.
        
        Args:
            auth_preference: 'app', 'user', or 'auto'
            app_id: GitHub App ID
            private_key_path: Path to GitHub App private key
            
        Returns:
            Authentication token or None
        """
        app_token = None
        user_token = os.getenv('GITHUB_USER_TOKEN')
        fallback_token = os.getenv('GITHUB_TOKEN')
        
        # Try to get GitHub App token if configured
        if get_github_app_token and app_id and private_key_path:
            try:
                # Convert API base URL to GitHub base URL for app authentication
                if self.base_url == "https://api.github.com":
                    github_base = "https://github.com"
                elif "/api/v3" in self.base_url:
                    github_base = self.base_url.replace('/api/v3', '')
                elif "://api." in self.base_url:
                    github_base = self.base_url.replace('://api.', '://')
                else:
                    github_base = self.base_url
                    
                app_token = get_github_app_token(app_id, private_key_path, github_base)
            except Exception as e:
                print(f"⚠️  GitHub App auth failed: {e}")
        
        # Apply authentication preference
        if auth_preference == 'app':
            if app_token:
                self.auth_method = "GitHub App"
                return app_token
            else:
                print("⚠️  GitHub App authentication preferred but not available, falling back")
        
        elif auth_preference == 'user':
            if user_token:
                self.auth_method = "User Token (GITHUB_USER_TOKEN)"
                return user_token
            elif fallback_token:
                self.auth_method = "User Token (GITHUB_TOKEN)"
                return fallback_token
            else:
                print("⚠️  User token authentication preferred but not available, falling back")
        
        # Auto mode or fallback logic
        if auth_preference == 'auto':
            # For user repos access, prefer user token if available
            if user_token:
                self.auth_method = "User Token (GITHUB_USER_TOKEN) - Auto"
                return user_token
            # For org-level access, prefer app token
            elif app_token and self.org:
                self.auth_method = "GitHub App - Auto"
                return app_token
            # Fall back to any available token
            elif fallback_token:
                self.auth_method = "Fallback Token (GITHUB_TOKEN) - Auto"
                return fallback_token
            elif app_token:
                self.auth_method = "GitHub App - Auto (fallback)"
                return app_token
        
        # Final fallback for failed preferences
        if app_token:
            self.auth_method = "GitHub App (fallback)"
            return app_token
        elif user_token:
            self.auth_method = "User Token (GITHUB_USER_TOKEN) - fallback"
            return user_token
        elif fallback_token:
            self.auth_method = "Fallback Token (GITHUB_TOKEN)"
            return fallback_token
        
        return None
    
    def search_files(self, 
                    query: str,
                    repo: Optional[str] = None,
                    org: Optional[str] = None,
                    path: Optional[str] = None,
                    extension: Optional[str] = None,
                    limit: int = 100) -> List[FileInfo]:
        """
        Search for files using GitHub's search API.
        
        Args:
            query: Search query (filename or partial filename)
            repo: Specific repository name (if None, searches across org)
            org: Organization name (defaults to self.org)
            path: Limit search to specific path
            extension: File extension filter (e.g., 'py', 'js')
            limit: Maximum results to return
            
        Returns:
            List of FileInfo objects
        """
        try:
            # Build search query
            search_parts = [query]
            
            if repo:
                org = org or self.org
                if org:
                    search_parts.append(f"repo:{org}/{repo}")
                else:
                    search_parts.append(f"repo:{repo}")
            elif org or self.org:
                search_parts.append(f"org:{org or self.org}")
            
            if path:
                search_parts.append(f"path:{path}")
            
            if extension:
                search_parts.append(f"extension:{extension}")
            
            search_query = " ".join(search_parts)
            
            # Perform search
            results = self.github.search_code(search_query)
            
            files = []
            for i, item in enumerate(results):
                if i >= limit:
                    break
                    
                file_info = FileInfo(
                    name=item.name,
                    path=item.path,
                    size=item.size if hasattr(item, 'size') else 0,
                    sha=item.sha,
                    download_url=item.download_url,
                    html_url=item.html_url,
                    type='file'
                )
                files.append(file_info)
            
            return files
            
        except GithubException as e:
            print(f"❌ Search error: {e}")
            return []
    
    def search_content(self,
                      query: str,
                      repo: Optional[str] = None,
                      org: Optional[str] = None,
                      path: Optional[str] = None,
                      extension: Optional[str] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for content within files using GitHub's search API.
        
        Args:
            query: Content to search for
            repo: Specific repository name
            org: Organization name
            path: Limit search to specific path
            extension: File extension filter
            limit: Maximum results to return
            
        Returns:
            List of search results with content matches
        """
        try:
            # Build search query - same as search_files but searches content
            search_parts = [query]
            
            if repo:
                org = org or self.org
                if org:
                    search_parts.append(f"repo:{org}/{repo}")
                else:
                    search_parts.append(f"repo:{repo}")
            elif org or self.org:
                search_parts.append(f"org:{org or self.org}")
            
            if path:
                search_parts.append(f"path:{path}")
            
            if extension:
                search_parts.append(f"extension:{extension}")
            
            search_query = " ".join(search_parts)
            
            # Perform content search
            results = self.github.search_code(search_query)
            
            matches = []
            for i, item in enumerate(results):
                if i >= limit:
                    break
                
                match_info = {
                    'file': {
                        'name': item.name,
                        'path': item.path,
                        'repository': item.repository.full_name,
                        'sha': item.sha,
                        'html_url': item.html_url,
                        'download_url': item.download_url
                    },
                    'score': item.score if hasattr(item, 'score') else None,
                    'repository_info': {
                        'name': item.repository.name,
                        'full_name': item.repository.full_name,
                        'description': item.repository.description,
                        'private': item.repository.private
                    }
                }
                matches.append(match_info)
            
            return matches
            
        except GithubException as e:
            print(f"❌ Content search error: {e}")
            return []
    
    def search_issues(self,
                     query: str,
                     repo: Optional[str] = None,
                     org: Optional[str] = None,
                     state: Optional[str] = None,
                     labels: Optional[List[str]] = None,
                     sort: Optional[str] = None,
                     order: Optional[str] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for issues and pull requests using GitHub's search API.
        
        Args:
            query: Search query
            repo: Specific repository name
            org: Organization name
            state: Issue state ('open', 'closed')
            labels: List of label names to filter by
            sort: Sort order ('comments', 'created', 'updated')
            order: Order ('asc', 'desc')
            limit: Maximum results to return
            
        Returns:
            List of issue/PR search results
        """
        try:
            # Build search query
            search_parts = [query]
            
            if repo:
                org = org or self.org
                if org:
                    search_parts.append(f"repo:{org}/{repo}")
                else:
                    search_parts.append(f"repo:{repo}")
            elif org or self.org:
                search_parts.append(f"org:{org or self.org}")
            
            if state:
                search_parts.append(f"state:{state}")
            
            if labels:
                for label in labels:
                    search_parts.append(f"label:{label}")
            
            search_query = " ".join(search_parts)
            
            # Perform search
            results = self.github.search_issues(search_query, sort=sort, order=order)
            
            issues = []
            for i, item in enumerate(results):
                if i >= limit:
                    break
                
                issue_info = {
                    'number': item.number,
                    'title': item.title,
                    'body': item.body,
                    'state': item.state,
                    'user': {
                        'login': item.user.login,
                        'html_url': item.user.html_url
                    } if item.user else None,
                    'labels': [{'name': label.name, 'color': label.color} for label in item.labels],
                    'assignees': [{'login': assignee.login} for assignee in item.assignees] if item.assignees else [],
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None,
                    'closed_at': item.closed_at.isoformat() if item.closed_at else None,
                    'html_url': item.html_url,
                    'repository': {
                        'name': item.repository.name,
                        'full_name': item.repository.full_name,
                        'html_url': item.repository.html_url
                    } if hasattr(item, 'repository') and item.repository else None,
                    'pull_request': item.pull_request is not None,
                    'score': item.score if hasattr(item, 'score') else None
                }
                issues.append(issue_info)
            
            return issues
            
        except GithubException as e:
            print(f"❌ Issues search error: {e}")
            return []

    def search_commits(self,
                      query: str,
                      repo: Optional[str] = None,
                      org: Optional[str] = None,
                      author: Optional[str] = None,
                      committer: Optional[str] = None,
                      sort: Optional[str] = None,
                      order: Optional[str] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for commits using GitHub's search API.
        
        Args:
            query: Search query
            repo: Specific repository name
            org: Organization name
            author: Commit author
            committer: Commit committer
            sort: Sort order ('author-date', 'committer-date')
            order: Order ('asc', 'desc')
            limit: Maximum results to return
            
        Returns:
            List of commit search results
        """
        try:
            # Build search query
            search_parts = [query]
            
            if repo:
                org = org or self.org
                if org:
                    search_parts.append(f"repo:{org}/{repo}")
                else:
                    search_parts.append(f"repo:{repo}")
            elif org or self.org:
                search_parts.append(f"org:{org or self.org}")
            
            if author:
                search_parts.append(f"author:{author}")
            
            if committer:
                search_parts.append(f"committer:{committer}")
            
            search_query = " ".join(search_parts)
            
            # Perform search
            results = self.github.search_commits(search_query, sort=sort, order=order)
            
            commits = []
            for i, item in enumerate(results):
                if i >= limit:
                    break
                
                commit_info = {
                    'sha': item.sha,
                    'message': item.commit.message,
                    'author': {
                        'name': item.commit.author.name,
                        'email': item.commit.author.email,
                        'date': item.commit.author.date.isoformat() if item.commit.author.date else None
                    } if item.commit.author else None,
                    'committer': {
                        'name': item.commit.committer.name,
                        'email': item.commit.committer.email,
                        'date': item.commit.committer.date.isoformat() if item.commit.committer.date else None
                    } if item.commit.committer else None,
                    'html_url': item.html_url,
                    'repository': {
                        'name': item.repository.name,
                        'full_name': item.repository.full_name,
                        'html_url': item.repository.html_url
                    } if hasattr(item, 'repository') and item.repository else None,
                    'score': item.score if hasattr(item, 'score') else None
                }
                commits.append(commit_info)
            
            return commits
            
        except GithubException as e:
            print(f"❌ Commits search error: {e}")
            return []

    def search_repositories(self,
                           query: str,
                           org: Optional[str] = None,
                           language: Optional[str] = None,
                           sort: Optional[str] = None,
                           order: Optional[str] = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for repositories using GitHub's search API.
        
        Args:
            query: Search query
            org: Organization name
            language: Programming language filter
            sort: Sort order ('stars', 'forks', 'updated')
            order: Order ('asc', 'desc')
            limit: Maximum results to return
            
        Returns:
            List of repository search results
        """
        try:
            # Build search query
            search_parts = [query]
            
            if org or self.org:
                search_parts.append(f"org:{org or self.org}")
            
            if language:
                search_parts.append(f"language:{language}")
            
            search_query = " ".join(search_parts)
            
            # Perform search
            results = self.github.search_repositories(search_query, sort=sort, order=order)
            
            repositories = []
            for i, item in enumerate(results):
                if i >= limit:
                    break
                
                repo_info = {
                    'name': item.name,
                    'full_name': item.full_name,
                    'description': item.description,
                    'private': item.private,
                    'html_url': item.html_url,
                    'clone_url': item.clone_url,
                    'language': item.language,
                    'stars': item.stargazers_count,
                    'forks': item.forks_count,
                    'open_issues': item.open_issues_count,
                    'size': item.size,
                    'default_branch': item.default_branch,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None,
                    'pushed_at': item.pushed_at.isoformat() if item.pushed_at else None,
                    'owner': {
                        'login': item.owner.login,
                        'type': item.owner.type,
                        'html_url': item.owner.html_url
                    } if item.owner else None,
                    'topics': item.get_topics() if hasattr(item, 'get_topics') else [],
                    'score': item.score if hasattr(item, 'score') else None
                }
                repositories.append(repo_info)
            
            return repositories
            
        except GithubException as e:
            print(f"❌ Repositories search error: {e}")
            return []

    def search_users(self,
                    query: str,
                    type: Optional[str] = None,
                    sort: Optional[str] = None,
                    order: Optional[str] = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for users using GitHub's search API.
        
        Args:
            query: Search query
            type: User type ('user', 'org')
            sort: Sort order ('followers', 'repositories', 'joined')
            order: Order ('asc', 'desc')
            limit: Maximum results to return
            
        Returns:
            List of user search results
        """
        try:
            # Build search query
            search_parts = [query]
            
            if type:
                search_parts.append(f"type:{type}")
            
            search_query = " ".join(search_parts)
            
            # Perform search
            results = self.github.search_users(search_query, sort=sort, order=order)
            
            users = []
            for i, item in enumerate(results):
                if i >= limit:
                    break
                
                user_info = {
                    'login': item.login,
                    'name': item.name,
                    'email': item.email,
                    'bio': item.bio,
                    'company': item.company,
                    'location': item.location,
                    'blog': item.blog,
                    'html_url': item.html_url,
                    'avatar_url': item.avatar_url,
                    'type': item.type,
                    'public_repos': item.public_repos,
                    'followers': item.followers,
                    'following': item.following,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None,
                    'score': item.score if hasattr(item, 'score') else None
                }
                users.append(user_info)
            
            return users
            
        except GithubException as e:
            print(f"❌ Users search error: {e}")
            return []

    def search_topics(self,
                     query: str,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for topics using GitHub's search API.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of topic search results
        """
        try:
            # Perform search
            results = self.github.search_topics(query)
            
            topics = []
            for i, item in enumerate(results):
                if i >= limit:
                    break
                
                topic_info = {
                    'name': item.name,
                    'display_name': item.display_name,
                    'short_description': item.short_description,
                    'description': item.description,
                    'created_by': item.created_by,
                    'released': item.released,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None,
                    'featured': item.featured,
                    'curated': item.curated,
                    'score': item.score if hasattr(item, 'score') else None
                }
                topics.append(topic_info)
            
            return topics
            
        except GithubException as e:
            print(f"❌ Topics search error: {e}")
            return []
    
    def list_repositories(self, 
                         org: Optional[str] = None,
                         type: str = 'all',
                         sort: str = 'updated',
                         limit: Optional[int] = None) -> List[RepositoryInfo]:
        """
        List repositories in an organization or for authenticated user.
        
        Now with intelligent fallback: if 'org' fails (e.g., it's actually a username),
        automatically tries to list that user's repositories instead.
        
        Args:
            org: Organization name or username (if None, lists authenticated user repos)
            type: Repository type ('all', 'public', 'private', 'member')
            sort: Sort order ('created', 'updated', 'pushed', 'full_name')
            limit: Maximum number of repositories to return
            
        Returns:
            List of RepositoryInfo objects
        """
        try:
            org = org or self.org
            
            if org:
                # First, try as an organization
                try:
                    github_org = self.github.get_organization(org)
                    repos = github_org.get_repos(type=type, sort=sort)
                    source_type = "organization"
                except GithubException as e:
                    # If org lookup fails, try as a user instead
                    if e.status == 404:
                        print(f"💡 '{org}' not found as organization, trying as user...")
                        try:
                            github_user = self.github.get_user(org)
                            repos = github_user.get_repos(type=type, sort=sort)
                            source_type = "user"
                        except GithubException as user_e:
                            if user_e.status == 404:
                                print(f"❌ '{org}' not found as organization or user")
                                return []
                            else:
                                raise user_e
                    else:
                        raise e
            else:
                # No org specified - use authenticated user
                repos = self.github.get_user().get_repos(type=type, sort=sort)
                source_type = "authenticated user"
            
            repo_list = []
            for i, repo in enumerate(repos):
                if limit and i >= limit:
                    break
                
                # Get language breakdown
                try:
                    languages = repo.get_languages()
                except:
                    languages = {}
                
                repo_info = RepositoryInfo(
                    name=repo.name,
                    full_name=repo.full_name,
                    description=repo.description,
                    private=repo.private,
                    default_branch=repo.default_branch,
                    language=repo.language,
                    languages=languages,
                    size=repo.size,
                    stars=repo.stargazers_count,
                    forks=repo.forks_count,
                    open_issues=repo.open_issues_count,
                    created_at=repo.created_at,
                    updated_at=repo.updated_at,
                    clone_url=repo.clone_url,
                    html_url=repo.html_url,
                    topics=repo.get_topics()
                )
                repo_list.append(repo_info)
            
            if org and source_type == "user":
                print(f"✅ Listed {len(repo_list)} repositories for user '{org}'")
            elif org and source_type == "organization":
                print(f"✅ Listed {len(repo_list)} repositories for organization '{org}'")
            
            return repo_list
            
        except GithubException as e:
            print(f"❌ Error listing repositories: {e}")
            return []
    
    def get_repository_info(self, 
                           repo_name: str,
                           org: Optional[str] = None) -> Optional[RepositoryInfo]:
        """
        Get detailed information about a specific repository.
        
        Args:
            repo_name: Repository name
            org: Organization name
            
        Returns:
            RepositoryInfo object or None if not found
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            
            # Get language breakdown
            try:
                languages = repo.get_languages()
            except:
                languages = {}
            
            return RepositoryInfo(
                name=repo.name,
                full_name=repo.full_name,
                description=repo.description,
                private=repo.private,
                default_branch=repo.default_branch,
                language=repo.language,
                languages=languages,
                size=repo.size,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                open_issues=repo.open_issues_count,
                created_at=repo.created_at,
                updated_at=repo.updated_at,
                clone_url=repo.clone_url,
                html_url=repo.html_url,
                topics=repo.get_topics()
            )
            
        except GithubException as e:
            print(f"❌ Error getting repository info: {e}")
            return None
    
    def get_contributors(self,
                        repo_name: str,
                        org: Optional[str] = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get contributor information for a repository.
        
        Args:
            repo_name: Repository name
            org: Organization name
            limit: Maximum number of contributors to return
            
        Returns:
            List of contributor information
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            contributors = repo.get_contributors()
            
            contributor_list = []
            for i, contributor in enumerate(contributors):
                if i >= limit:
                    break
                
                contributor_info = {
                    'login': contributor.login,
                    'name': contributor.name,
                    'email': contributor.email,
                    'contributions': contributor.contributions,
                    'avatar_url': contributor.avatar_url,
                    'html_url': contributor.html_url,
                    'type': contributor.type,
                    'company': getattr(contributor, 'company', None),
                    'blog': getattr(contributor, 'blog', None),
                    'location': getattr(contributor, 'location', None),
                    'bio': getattr(contributor, 'bio', None)
                }
                contributor_list.append(contributor_info)
            
            return contributor_list
            
        except GithubException as e:
            print(f"❌ Error getting contributors: {e}")
            return []
    
    def get_repository_tree(self,
                           repo_name: str,
                           org: Optional[str] = None,
                           branch: Optional[str] = None,
                           recursive: bool = True) -> Dict[str, Any]:
        """
        Get complete file tree of repository as nested dictionary.
        
        Args:
            repo_name: Repository name
            org: Organization name
            branch: Branch name (defaults to default branch)
            recursive: Whether to get full tree recursively
            
        Returns:
            Nested dictionary representing file structure
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            branch = branch or repo.default_branch
            
            # Get the tree
            tree = repo.get_git_tree(sha=branch, recursive=recursive)
            
            # Build nested structure
            file_tree = {}
            
            for item in tree.tree:
                path_parts = item.path.split('/')
                current_level = file_tree
                
                # Navigate/create nested structure
                for i, part in enumerate(path_parts):
                    if i == len(path_parts) - 1:  # Last part (file/dir name)
                        current_level[part] = {
                            'type': item.type,
                            'size': item.size,
                            'sha': item.sha,
                            'url': item.url,
                            'path': item.path
                        }
                        
                        # If it's a directory, initialize as dict for potential children
                        if item.type == 'tree':
                            current_level[part]['children'] = {}
                    else:
                        # Intermediate directory
                        if part not in current_level:
                            current_level[part] = {
                                'type': 'tree',
                                'children': {}
                            }
                        current_level = current_level[part]['children']
            
            return {
                'repository': full_name,
                'branch': branch,
                'tree': file_tree,
                'total_files': len([item for item in tree.tree if item.type == 'blob']),
                'total_dirs': len([item for item in tree.tree if item.type == 'tree'])
            }
            
        except GithubException as e:
            print(f"❌ Error getting repository tree: {e}")
            return {}
    
    def get_repository_tree_ascii(self,
                                 repo_name: str,
                                 org: Optional[str] = None,
                                 branch: Optional[str] = None,
                                 show_file_sizes: bool = True,
                                 max_depth: Optional[int] = None,
                                 sort_by: str = 'name') -> str:
        """
        Get repository structure as ASCII tree visualization.
        
        Perfect for AI agents to quickly understand project organization.
        Similar to the Unix 'tree' command output.
        
        Args:
            repo_name: Repository name
            org: Organization name
            branch: Branch name (defaults to default branch)
            show_file_sizes: Whether to show file sizes in the tree
            max_depth: Maximum depth to show (None for unlimited)
            sort_by: Sort order ('name', 'size', 'type')
            
        Returns:
            ASCII tree representation of repository structure
        """
        try:
            # Get the nested tree structure
            tree_data = self.get_repository_tree(repo_name, org=org, branch=branch, recursive=True)
            
            if not tree_data or 'tree' not in tree_data:
                return f"❌ Could not fetch repository tree for {repo_name}"
            
            # Build ASCII tree
            lines = []
            repo_name_display = tree_data.get('repository', repo_name)
            
            # Header
            lines.append(f"{repo_name_display}/")
            
            # Generate tree
            tree_lines = self._generate_ascii_tree(
                tree_data['tree'], 
                show_file_sizes=show_file_sizes,
                max_depth=max_depth,
                current_depth=0,
                sort_by=sort_by
            )
            lines.extend(tree_lines)
            
            # Footer with summary
            lines.append("")
            lines.append(f"📊 {tree_data['total_dirs']} directories, {tree_data['total_files']} files")
            if tree_data.get('branch'):
                lines.append(f"🌿 Branch: {tree_data['branch']}")
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"❌ Error generating ASCII tree: {e}"
    
    def _generate_ascii_tree(self, 
                           tree_dict: Dict[str, Any], 
                           prefix: str = "",
                           show_file_sizes: bool = True,
                           max_depth: Optional[int] = None,
                           current_depth: int = 0,
                           sort_by: str = 'name') -> List[str]:
        """Helper method to recursively generate ASCII tree lines."""
        
        if max_depth is not None and current_depth >= max_depth:
            return []
        
        lines = []
        items = list(tree_dict.items())
        
        # Sort items
        if sort_by == 'type':
            # Directories first, then files, both alphabetically
            items.sort(key=lambda x: (x[1].get('type') != 'tree', x[0].lower()))
        elif sort_by == 'size':
            # Sort by size (directories considered size 0)
            items.sort(key=lambda x: (x[1].get('size') or 0, x[0].lower()), reverse=True)
        else:  # sort_by == 'name'
            items.sort(key=lambda x: x[0].lower())
        
        for i, (name, info) in enumerate(items):
            is_last = i == len(items) - 1
            
            # Choose the right prefix symbols
            if is_last:
                current_prefix = "└── "
                next_prefix = "    "
            else:
                current_prefix = "├── "
                next_prefix = "│   "
            
            # Build the line for this item
            line = prefix + current_prefix + name
            
            # Add file size if it's a file and we're showing sizes
            if info.get('type') == 'blob' and show_file_sizes and info.get('size') is not None:
                size = info['size']
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/(1024*1024):.1f}MB"
                line += f" ({size_str})"
            elif info.get('type') == 'tree':
                line += "/"
            
            lines.append(line)
            
            # Recursively handle subdirectories
            if info.get('type') == 'tree' and 'children' in info and info['children']:
                sublines = self._generate_ascii_tree(
                    info['children'],
                    prefix + next_prefix,
                    show_file_sizes=show_file_sizes,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    sort_by=sort_by
                )
                lines.extend(sublines)
        
        return lines
    
    def list_directory(self,
                      repo_name: str,
                      directory_path: str = "",
                      org: Optional[str] = None,
                      branch: Optional[str] = None) -> List[Dict[str, Any]]:
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
            List of directory contents with metadata
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            
            # Get directory contents - only pass ref if branch is specified
            if branch:
                contents = repo.get_contents(directory_path, ref=branch)
            else:
                contents = repo.get_contents(directory_path)
            
            # Handle single file case (shouldn't happen for directories but just in case)
            if not isinstance(contents, list):
                return [{
                    'name': contents.name,
                    'path': contents.path,
                    'type': 'file',
                    'size': contents.size,
                    'sha': contents.sha,
                    'download_url': contents.download_url,
                    'html_url': contents.html_url
                }]
            
            # Process directory contents
            directory_items = []
            for item in contents:
                item_info = {
                    'name': item.name,
                    'path': item.path,
                    'type': 'directory' if item.type == 'dir' else 'file',
                    'size': item.size if item.type == 'file' else None,
                    'sha': item.sha,
                    'download_url': item.download_url if item.type == 'file' else None,
                    'html_url': item.html_url
                }
                directory_items.append(item_info)
            
            # Sort by type (directories first) then by name
            directory_items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
            
            return directory_items
            
        except GithubException as e:
            if e.status == 404:
                print(f"❌ Directory not found: {directory_path}")
                return []
            else:
                print(f"❌ Error listing directory {directory_path}: {e}")
                return []
        except Exception as e:
            print(f"❌ Unexpected error listing directory {directory_path}: {e}")
            return []
    
    def get_file(self,
                repo_name: str,
                file_path: str,
                org: Optional[str] = None,
                branch: Optional[str] = None,
                decode_content: bool = True) -> Optional[FileInfo]:
        """
        Get a specific file from repository.
        
        Args:
            repo_name: Repository name
            file_path: Path to file in repository
            org: Organization name
            branch: Branch name (defaults to default branch)
            decode_content: Whether to decode base64 content
            
        Returns:
            FileInfo object with content or None if not found
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            
            # Get file content - only pass ref if branch is specified
            if branch:
                file_content = repo.get_contents(file_path, ref=branch)
            else:
                file_content = repo.get_contents(file_path)
            
            # Handle if it's a directory
            if isinstance(file_content, list):
                return None
            
            # Decode content if requested and it's a file
            content = None
            if decode_content and file_content.content:
                try:
                    content = base64.b64decode(file_content.content).decode('utf-8')
                except UnicodeDecodeError:
                    # Binary file - keep as base64
                    content = file_content.content
            
            return FileInfo(
                name=file_content.name,
                path=file_content.path,
                size=file_content.size,
                sha=file_content.sha,
                download_url=file_content.download_url,
                html_url=file_content.html_url,
                type=file_content.type,
                content=content
            )
            
        except GithubException as e:
            if e.status == 404:
                return None  # File not found - don't print error for this case
            else:
                print(f"❌ GitHub error getting file {file_path}: {e.status} - {e.data}")
                return None
        except Exception as e:
            print(f"❌ Unexpected error getting file {file_path}: {repr(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_files_as_codeblock(self,
                              repo_name: str,
                              file_paths: List[str],
                              org: Optional[str] = None,
                              branch: Optional[str] = None,
                              support_globs: bool = True,
                              include_line_numbers: bool = False) -> str:
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
            Formatted string with all files stitched together
        """
        try:
            import fnmatch
            
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            # Expand glob patterns if requested
            expanded_paths = []
            if support_globs:
                # Get repository tree to match against glob patterns
                tree = self.get_repository_tree(repo_name, org=org, branch=branch, recursive=True)
                if tree and 'tree' in tree:
                    all_file_paths = self._extract_file_paths_from_tree(tree['tree'])
                    
                    for pattern in file_paths:
                        if '*' in pattern or '?' in pattern or '[' in pattern:
                            # It's a glob pattern
                            matches = [path for path in all_file_paths if fnmatch.fnmatch(path, pattern)]
                            expanded_paths.extend(matches)
                        else:
                            # Regular file path
                            expanded_paths.append(pattern)
                else:
                    # Fallback to original paths if tree fetch fails
                    expanded_paths = file_paths
            else:
                expanded_paths = file_paths
            
            # Remove duplicates while preserving order
            seen = set()
            unique_paths = []
            for path in expanded_paths:
                if path not in seen:
                    seen.add(path)
                    unique_paths.append(path)
            
            # Fetch all files
            result_blocks = []
            successful_files = 0
            failed_files = 0
            
            for file_path in unique_paths:
                file_info = self.get_file(repo_name, file_path, org=org, branch=branch)
                
                if file_info and file_info.content:
                    # Determine file extension for syntax highlighting
                    extension = self._get_file_extension_for_highlighting(file_info.name)
                    
                    # Build the code block
                    block_parts = []
                    
                    # File path header
                    repo_path = f"{full_name}/{file_info.path}"
                    block_parts.append(repo_path)
                    block_parts.append("")  # Empty line
                    
                    # Code block start
                    block_parts.append(f"```{extension}")
                    
                    # File content (with optional line numbers)
                    if include_line_numbers:
                        lines = file_info.content.split('\n')
                        numbered_lines = []
                        for i, line in enumerate(lines, 1):
                            numbered_lines.append(f"{i:4d}: {line}")
                        block_parts.append('\n'.join(numbered_lines))
                    else:
                        block_parts.append(file_info.content)
                    
                    # Code block end
                    block_parts.append("```")
                    block_parts.append("")  # Empty line for separation
                    
                    result_blocks.append('\n'.join(block_parts))
                    successful_files += 1
                else:
                    # File not found or couldn't be read
                    failed_files += 1
                    if file_info is None:
                        result_blocks.append(f"# ❌ File not found: {file_path}\n")
                    else:
                        result_blocks.append(f"# ❌ Could not read file: {file_path} (binary or empty)\n")
            
            # Combine all blocks
            final_result = '\n'.join(result_blocks)
            
            # Add summary header
            summary = f"# 📁 Repository: {full_name}\n"
            summary += f"# 📊 Files: {successful_files} successful, {failed_files} failed\n"
            if branch:
                summary += f"# 🌿 Branch: {branch}\n"
            summary += f"# 🕒 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            return summary + final_result
            
        except Exception as e:
            print(f"❌ Error creating codeblock: {e}")
            return f"# ❌ Error: Could not fetch files - {e}\n"
    
    def _extract_file_paths_from_tree(self, tree_dict: Dict[str, Any], current_path: str = "") -> List[str]:
        """Helper method to extract all file paths from repository tree."""
        file_paths = []
        
        for name, info in tree_dict.items():
            item_path = f"{current_path}/{name}" if current_path else name
            
            if info.get('type') == 'blob':  # It's a file
                file_paths.append(item_path)
            elif info.get('type') == 'tree' and 'children' in info:  # It's a directory
                file_paths.extend(self._extract_file_paths_from_tree(info['children'], item_path))
        
        return file_paths
    
    def _get_file_extension_for_highlighting(self, filename: str) -> str:
        """Helper method to determine syntax highlighting based on file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'bash',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.html': 'html',
            '.htm': 'html',
            '.xml': 'xml',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.rst': 'rst',
            '.txt': 'text',
            '.log': 'text',
            '.dockerfile': 'dockerfile',
            '.makefile': 'makefile',
            '.mk': 'makefile',
            '.r': 'r',
            '.R': 'r',
            '.scala': 'scala',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.dart': 'dart',
            '.lua': 'lua',
            '.perl': 'perl',
            '.pl': 'perl',
            '.vim': 'vim',
        }
        
        # Get file extension
        ext = None
        if '.' in filename:
            ext = '.' + filename.split('.')[-1].lower()
        
        # Special cases for files without extensions
        lower_name = filename.lower()
        if lower_name in ['dockerfile', 'makefile', 'rakefile', 'gemfile']:
            return lower_name
        
        return extension_map.get(ext, 'text')
    
    def get_pull_requests(self,
                         repo_name: str,
                         org: Optional[str] = None,
                         state: str = 'open',
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get pull request information for repository.
        
        Args:
            repo_name: Repository name
            org: Organization name
            state: PR state ('open', 'closed', 'all')
            limit: Maximum number of PRs to return
            
        Returns:
            List of pull request information
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            pulls = repo.get_pulls(state=state, sort='updated', direction='desc')
            
            pr_list = []
            for i, pr in enumerate(pulls):
                if i >= limit:
                    break
                
                pr_info = {
                    'number': pr.number,
                    'title': pr.title,
                    'body': pr.body,
                    'state': pr.state,
                    'user': {
                        'login': pr.user.login,
                        'name': pr.user.name,
                        'avatar_url': pr.user.avatar_url
                    },
                    'created_at': pr.created_at,
                    'updated_at': pr.updated_at,
                    'closed_at': pr.closed_at,
                    'merged_at': pr.merged_at,
                    'html_url': pr.html_url,
                    'head': {
                        'ref': pr.head.ref,
                        'sha': pr.head.sha
                    },
                    'base': {
                        'ref': pr.base.ref,
                        'sha': pr.base.sha
                    },
                    'mergeable': pr.mergeable,
                    'merged': pr.merged,
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                    'changed_files': pr.changed_files,
                    'comments': pr.comments,
                    'review_comments': pr.review_comments,
                    'commits': pr.commits
                }
                pr_list.append(pr_info)
            
            return pr_list
            
        except GithubException as e:
            print(f"❌ Error getting pull requests: {e}")
            return []
    
    def get_commits(self,
                   repo_name: str,
                   org: Optional[str] = None,
                   branch: Optional[str] = None,
                   limit: int = 50,
                   since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get commit information for repository.
        
        Args:
            repo_name: Repository name
            org: Organization name
            branch: Branch name (defaults to default branch)
            limit: Maximum number of commits to return
            since: Only commits after this date
            
        Returns:
            List of commit information
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            
            kwargs = {}
            if branch:
                kwargs['sha'] = branch
            if since:
                kwargs['since'] = since
            
            commits = repo.get_commits(**kwargs)
            
            commit_list = []
            for i, commit in enumerate(commits):
                if i >= limit:
                    break
                
                commit_info = {
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'author': {
                        'name': commit.commit.author.name,
                        'email': commit.commit.author.email,
                        'date': commit.commit.author.date
                    },
                    'committer': {
                        'name': commit.commit.committer.name,
                        'email': commit.commit.committer.email,
                        'date': commit.commit.committer.date
                    },
                    'html_url': commit.html_url,
                    'stats': {
                        'total': commit.stats.total,
                        'additions': commit.stats.additions,
                        'deletions': commit.stats.deletions
                    } if commit.stats else None,
                    'files_changed': sum(1 for _ in commit.files) if commit.files else 0,
                    'parents': [parent.sha for parent in commit.parents]
                }
                
                # Add GitHub user info if available
                if commit.author:
                    commit_info['github_author'] = {
                        'login': commit.author.login,
                        'avatar_url': commit.author.avatar_url
                    }
                
                commit_list.append(commit_info)
            
            return commit_list
            
        except GithubException as e:
            print(f"❌ Error getting commits: {e}")
            return []
    
    def get_issues(self,
                  repo_name: str,
                  org: Optional[str] = None,
                  state: str = 'open',
                  labels: Optional[List[str]] = None,
                  limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get issues for repository.
        
        Args:
            repo_name: Repository name
            org: Organization name
            state: Issue state ('open', 'closed', 'all')
            labels: Filter by labels
            limit: Maximum number of issues to return
            
        Returns:
            List of issue information
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            repo = self.github.get_repo(full_name)
            
            kwargs = {'state': state, 'sort': 'updated', 'direction': 'desc'}
            if labels:
                kwargs['labels'] = labels
            
            issues = repo.get_issues(**kwargs)
            
            issue_list = []
            for i, issue in enumerate(issues):
                if i >= limit:
                    break
                
                # Skip pull requests (they appear in issues API)
                if issue.pull_request:
                    continue
                
                issue_info = {
                    'number': issue.number,
                    'title': issue.title,
                    'body': issue.body,
                    'state': issue.state,
                    'user': {
                        'login': issue.user.login,
                        'name': issue.user.name,
                        'avatar_url': issue.user.avatar_url
                    },
                    'assignees': [
                        {
                            'login': assignee.login,
                            'name': assignee.name
                        } for assignee in issue.assignees
                    ],
                    'labels': [label.name for label in issue.labels],
                    'created_at': issue.created_at,
                    'updated_at': issue.updated_at,
                    'closed_at': issue.closed_at,
                    'html_url': issue.html_url,
                    'comments': issue.comments,
                    'milestone': {
                        'title': issue.milestone.title,
                        'description': issue.milestone.description,
                        'state': issue.milestone.state
                    } if issue.milestone else None
                }
                issue_list.append(issue_info)
            
            return issue_list
            
        except GithubException as e:
            print(f"❌ Error getting issues: {e}")
            return []
    
    def get_discussions(self,
                       repo_name: str,
                       org: Optional[str] = None,
                       limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get discussions for repository.
        
        Note: This requires the repository to have discussions enabled.
        Uses GraphQL API which has different rate limits.
        
        Args:
            repo_name: Repository name
            org: Organization name
            limit: Maximum number of discussions to return
            
        Returns:
            List of discussion information
        """
        try:
            org = org or self.org
            full_name = f"{org}/{repo_name}" if org else repo_name
            
            # GitHub Discussions requires GraphQL API
            # This is a simplified implementation - you might want to use
            # a dedicated GraphQL client for more complex queries
            
            query = """
            query($owner: String!, $name: String!, $first: Int!) {
                repository(owner: $owner, name: $name) {
                    discussions(first: $first, orderBy: {field: UPDATED_AT, direction: DESC}) {
                        nodes {
                            id
                            title
                            body
                            createdAt
                            updatedAt
                            url
                            author {
                                login
                                avatarUrl
                            }
                            category {
                                name
                                description
                            }
                            comments {
                                totalCount
                            }
                            upvoteCount
                            answerChosenAt
                            isAnswered
                        }
                    }
                }
            }
            """
            
            variables = {
                "owner": org,
                "name": repo_name,
                "first": limit
            }
            
            # Use PyGithub's internal session to make GraphQL request
            headers = {
                'Authorization': f'bearer {self.github._Github__requester._Requester__authorizationHeader.split()[1]}',
                'Content-Type': 'application/json'
            }
            
            response = self.github._Github__requester._Requester__httpSession.post(
                f"{self.github._Github__requester._Requester__base_url.replace('/api/v3', '')}/api/graphql",
                json={'query': query, 'variables': variables},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['repository']:
                    discussions = data['data']['repository']['discussions']['nodes']
                    
                    discussion_list = []
                    for discussion in discussions:
                        discussion_info = {
                            'id': discussion['id'],
                            'title': discussion['title'],
                            'body': discussion['body'],
                            'created_at': discussion['createdAt'],
                            'updated_at': discussion['updatedAt'],
                            'url': discussion['url'],
                            'author': {
                                'login': discussion['author']['login'] if discussion['author'] else None,
                                'avatar_url': discussion['author']['avatarUrl'] if discussion['author'] else None
                            },
                            'category': {
                                'name': discussion['category']['name'],
                                'description': discussion['category']['description']
                            },
                            'comments_count': discussion['comments']['totalCount'],
                            'upvotes': discussion['upvoteCount'],
                            'is_answered': discussion['isAnswered'],
                            'answer_chosen_at': discussion['answerChosenAt']
                        }
                        discussion_list.append(discussion_info)
                    
                    return discussion_list
                else:
                    print("❌ No discussions data or repository not found")
                    return []
            else:
                print(f"❌ GraphQL request failed: {response.status_code}")
                return []
            
        except Exception as e:
            print(f"❌ Error getting discussions: {e}")
            return []
    
    def get_auth_info(self) -> Dict[str, Any]:
        """
        Get information about current authentication method and capabilities.
        
        Returns:
            Dict with auth method, user info, and capabilities
        """
        try:
            user = self.github.get_user()
            
            # Determine if this is likely a user token or app token
            is_app_token = hasattr(user, 'type') and user.type == 'Bot'
            
            auth_info = {
                'method': self.auth_method or 'Unknown',
                'authenticated_as': user.login,
                'user_type': getattr(user, 'type', 'User'),
                'is_app_token': is_app_token,
                'api_rate_limit': {
                    'limit': self.github.rate_limiting[0],
                    'remaining': self.github.rate_limiting[1]
                },
                'capabilities': {
                    'can_access_private_repos': not is_app_token,  # User tokens can access user's private repos
                    'can_access_org_repos': True,  # Both can access org repos they have permission to
                    'recommended_for': 'personal repositories' if not is_app_token else 'organization repositories'
                }
            }
            
            return auth_info
            
        except Exception as e:
            return {
                'method': self.auth_method or 'Unknown',
                'error': str(e),
                'authenticated': False
            }


# Example usage and testing
if __name__ == "__main__":
    # Example initialization
    explorer = GitHubExplorer()
    
    # Test with a public repository
    repo_info = explorer.get_repository_info("pytorch", org="pytorch")
    if repo_info:
        print(f"Repository: {repo_info.name}")
        print(f"Description: {repo_info.description}")
        print(f"Language: {repo_info.language}")
        print(f"Stars: {repo_info.stars}") 