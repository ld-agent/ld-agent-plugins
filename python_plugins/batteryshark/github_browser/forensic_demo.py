#!/usr/bin/env python3
"""
GitHub Browser Forensic Analysis Demo
Demonstrates security and code review capabilities for AI agents
"""

import sys
sys.path.append('plugins')
from github_browser import *

def demo_basic_forensics():
    """Demo basic forensic analysis capabilities"""
    print('🔍 FORENSIC SECURITY ANALYSIS DEMO')
    print('=' * 50)

    # 1. Get repo info
    repo_info = get_repository_info_from_git_folder('./lexy', extract_repository_stats=True)
    print(f'📊 Analyzing: {repo_info["org"]}/{repo_info["repo_name"]}')
    print(f'📈 Total commits: {repo_info["repository_stats"]["total_commits"]}')
    print(f'👥 Contributors: {repo_info["repository_stats"]["total_contributors"]}')

    # 2. Investigate README.md changes
    print(f'\n🔍 INVESTIGATING FILE HISTORY')
    print('-' * 30)
    
    history = get_file_history('README.md', './lexy', limit=5)
    print(f'📄 README.md changed {history["total_commits"]} times')

    for i, commit in enumerate(history['commits'][:3]):
        print(f'  {i+1}. {commit["date"][:10]}: {commit["message"]} by {commit["author_name"]}')

    # 3. Get older version
    print(f'\n📋 COMPARING FILE VERSIONS')
    print('-' * 30)
    
    comparison = compare_file_versions('README.md', 'HEAD~1', 'HEAD', './lexy')
    if comparison and comparison['has_changes']:
        print(f'✅ Changes detected between commits')
        print(f'📝 Old: {comparison["commit1"]["message"]}')
        print(f'📝 New: {comparison["commit2"]["message"]}')
        print(f'📊 Diff preview: {len(comparison["diff"].splitlines())} lines changed')
    else:
        print('ℹ️  No changes between these commits')

    # 4. Search for specific patterns
    print(f'\n🔍 SEARCHING FOR SECURITY PATTERNS')
    print('-' * 30)
    
    # Look for any mentions of "Lexy" changes
    changes = search_file_changes('README.md', 'Lexy', './lexy')
    if changes:
        print(f'🔎 Found {changes["total_matches"]} commits mentioning "Lexy"')
        
        for commit in changes['commits_with_code_changes'][:2]:
            print(f'  📝 {commit["hash"][:8]}: {commit["message"]} by {commit["author"]}')
        
        for commit in changes['commits_with_message_mentions'][:2]:
            print(f'  💬 {commit["hash"][:8]}: {commit["message"]} by {commit["author_name"]}')

    print(f'\n✅ Forensic analysis complete!')

def demo_security_agent():
    """Demo AI security agent workflow"""
    print(f'\n🤖 AI SECURITY AGENT SIMULATION')
    print('=' * 50)
    
    class SimpleSecurityAgent:
        def __init__(self, repo_path):
            self.repo_path = repo_path
            # Common security-related terms to monitor
            self.security_patterns = [
                'password', 'secret', 'key', 'token', 'auth',
                'admin', 'root', 'config', 'api'
            ]
        
        def quick_security_scan(self, file_path):
            """Perform quick security pattern scan"""
            print(f'🔍 Scanning {file_path} for security patterns...')
            
            vulnerabilities_found = []
            
            for pattern in self.security_patterns:
                changes = search_file_changes(file_path, pattern, self.repo_path)
                if changes and changes['total_matches'] > 0:
                    vulnerabilities_found.append({
                        'pattern': pattern,
                        'matches': changes['total_matches'],
                        'recent_commits': changes['commits_with_code_changes'][:1]
                    })
            
            if vulnerabilities_found:
                print(f'⚠️  Found {len(vulnerabilities_found)} potential security-related patterns:')
                for vuln in vulnerabilities_found:
                    print(f'   - "{vuln["pattern"]}": {vuln["matches"]} matches')
                    if vuln['recent_commits']:
                        commit = vuln['recent_commits'][0]
                        print(f'     Most recent: {commit["message"]} by {commit["author"]}')
            else:
                print(f'✅ No obvious security patterns found in {file_path}')
            
            return vulnerabilities_found
        
        def investigate_file_ownership(self, file_path):
            """See who has been modifying critical files"""
            print(f'\n👥 Investigating file ownership for {file_path}')
            
            history = get_file_history(file_path, self.repo_path, limit=10)
            if history:
                authors = {}
                for commit in history['commits']:
                    author = commit['author_name']
                    if author not in authors:
                        authors[author] = 0
                    authors[author] += 1
                
                print(f'📊 File modified by {len(authors)} different authors:')
                for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True):
                    print(f'   - {author}: {count} commits')
            
            return history

    # Run security agent
    agent = SimpleSecurityAgent('./lexy')
    
    # Scan README.md for security patterns
    vulnerabilities = agent.quick_security_scan('README.md')
    
    # Investigate who has been changing the file
    ownership = agent.investigate_file_ownership('README.md')
    
    print(f'\n🎯 Security Agent Summary:')
    print(f'   - Patterns found: {len(vulnerabilities)}')
    print(f'   - File modifications tracked: {ownership["total_commits"] if ownership else 0}')

if __name__ == '__main__':
    try:
        demo_basic_forensics()
        demo_security_agent()
        
        print(f'\n🚀 FORENSIC ANALYSIS CAPABILITIES:')
        print(f'   ✅ File version history tracking')
        print(f'   ✅ Commit-level change analysis') 
        print(f'   ✅ Security pattern detection')
        print(f'   ✅ Author/ownership tracking')
        print(f'   ✅ Automated vulnerability investigation')
        print(f'\n💡 Perfect for AI-powered security audits and code review!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        print('Make sure you are in a directory with a "lexy" git repository') 