# 🔍 GitHub Browser: Forensic Analysis for Agentic Security & Code Review

## Overview

The GitHub Browser plugin now includes powerful **forensic analysis capabilities** that enable AI agents to perform deep security audits, bug investigations, and automated code review with unprecedented insight into code evolution and potential vulnerabilities.

## 🛡️ Security-Focused Use Cases

### 1. **Vulnerability Introduction Detection**
AI agents can automatically track when and how security vulnerabilities were introduced:

```python
# Agent detects a potential SQL injection vulnerability
vulnerable_file = "src/database/query_builder.py"

# 1. Find when the vulnerable code was introduced
changes = search_file_changes(vulnerable_file, "execute(")
print(f"Found {changes['total_matches']} commits that modified execute() calls")

# 2. Get the exact commit that introduced the issue
for commit in changes['commits_with_code_changes']:
    print(f"Potential introduction: {commit['hash']} by {commit['author']}")
    print(f"Message: {commit['message']}")
    print(f"Changes: {commit['changes']}")

# 3. Compare with safe version before the vulnerability
safe_version = get_file_at_commit(vulnerable_file, "HEAD~10")
current_version = get_file_at_commit(vulnerable_file, "HEAD")

# 4. Generate security diff report
comparison = compare_file_versions(vulnerable_file, "HEAD~10", "HEAD")
print("Security-relevant changes:")
print(comparison['diff'])
```

### 2. **Authentication & Authorization Audit Trail**
Track changes to critical security functions:

```python
# Audit authentication system changes
auth_files = ["src/auth/login.py", "src/auth/permissions.py", "src/middleware/auth.py"]

for auth_file in auth_files:
    print(f"\n🔐 Auditing {auth_file}")
    
    # Find all authentication-related changes
    auth_changes = search_file_changes(auth_file, "authenticate")
    token_changes = search_file_changes(auth_file, "token")
    permission_changes = search_file_changes(auth_file, "permission")
    
    # Generate security timeline
    history = get_file_history(auth_file, limit=20, include_patches=True)
    print(f"Authentication file modified {history['total_commits']} times")
    
    # Highlight recent critical changes
    for commit in history['commits'][:5]:
        if any(keyword in commit['message'].lower() for keyword in ['security', 'auth', 'login', 'token']):
            print(f"⚠️  SECURITY CHANGE: {commit['date']} - {commit['message']}")
```

### 3. **Dependency & Third-Party Code Analysis**
Monitor changes to critical dependencies and external integrations:

```python
# Track changes to package management and external APIs
security_files = [
    "requirements.txt", "package.json", "Gemfile", 
    "src/integrations/", "src/external/", "src/api/third_party.py"
]

for file_path in security_files:
    print(f"\n📦 Analyzing dependency changes in {file_path}")
    
    # Find when new dependencies were added
    dependency_history = get_file_history(file_path, limit=10)
    
    for commit in dependency_history['commits']:
        # Check for new packages or version changes
        old_version = get_file_at_commit(file_path, f"{commit['hash']}~1")
        new_version = get_file_at_commit(file_path, commit['hash'])
        
        if old_version and new_version:
            diff = compare_file_versions(file_path, f"{commit['hash']}~1", commit['hash'])
            if '+' in diff['diff']:  # New additions
                print(f"🚨 NEW DEPENDENCY: {commit['date']} - {commit['message']}")
                print(f"Changes: {diff['diff']}")
```

## 🤖 Agentic Code Review Workflows

### **Automated Security Review Agent**

```python
class SecurityReviewAgent:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.security_patterns = [
            "password", "secret", "key", "token", "auth", 
            "execute(", "eval(", "system(", "shell_exec",
            "sql", "query", "database"
        ]
    
    def perform_security_audit(self, target_files):
        """Comprehensive security audit using forensic analysis"""
        security_report = {
            'high_risk_changes': [],
            'authentication_timeline': [],
            'dependency_changes': [],
            'potential_vulnerabilities': []
        }
        
        for file_path in target_files:
            # 1. Analyze recent changes for security patterns
            for pattern in self.security_patterns:
                changes = search_file_changes(file_path, pattern)
                
                if changes['total_matches'] > 0:
                    security_report['potential_vulnerabilities'].append({
                        'file': file_path,
                        'pattern': pattern,
                        'commits': changes['commits_with_code_changes']
                    })
            
            # 2. Track authentication-related changes
            if 'auth' in file_path.lower() or 'login' in file_path.lower():
                auth_history = get_file_history(file_path, limit=15)
                security_report['authentication_timeline'].append({
                    'file': file_path,
                    'changes': auth_history['commits']
                })
            
            # 3. Find who has access to sensitive code
            blame_info = get_file_blame(file_path)
            if blame_info:
                sensitive_authors = set()
                for line in blame_info['blame_lines']:
                    if any(pattern in line['content'].lower() for pattern in self.security_patterns):
                        sensitive_authors.add(line['author'])
                
                if sensitive_authors:
                    security_report['high_risk_changes'].append({
                        'file': file_path,
                        'authors_with_sensitive_access': list(sensitive_authors)
                    })
        
        return security_report
    
    def investigate_vulnerability(self, file_path, vulnerability_pattern):
        """Deep dive investigation of a specific vulnerability"""
        print(f"🔍 Investigating {vulnerability_pattern} in {file_path}")
        
        # 1. Find when vulnerability was introduced
        changes = search_file_changes(file_path, vulnerability_pattern)
        
        # 2. Get the timeline of changes
        history = get_file_history(file_path, limit=20, include_patches=True)
        
        # 3. Find the "smoking gun" commit
        for commit in changes['commits_with_code_changes']:
            print(f"\n🚨 FOUND VULNERABILITY INTRODUCTION:")
            print(f"   Commit: {commit['hash']}")
            print(f"   Author: {commit['author']}")
            print(f"   Date: {commit['date']}")
            print(f"   Message: {commit['message']}")
            print(f"   Changes: {commit['changes']}")
            
            # 4. Get the file before and after
            before = get_file_at_commit(file_path, f"{commit['hash']}~1")
            after = get_file_at_commit(file_path, commit['hash'])
            
            if before and after:
                diff = compare_file_versions(file_path, f"{commit['hash']}~1", commit['hash'])
                print(f"\n📋 FULL DIFF:")
                print(diff['diff'])
        
        # 5. Check who else has touched this code
        blame = get_file_blame(file_path)
        if blame:
            vulnerable_lines = [
                line for line in blame['blame_lines'] 
                if vulnerability_pattern.lower() in line['content'].lower()
            ]
            
            print(f"\n👥 AUTHORS OF VULNERABLE CODE:")
            for line in vulnerable_lines:
                print(f"   Line {line['line_number']}: {line['author']} - {line['date']}")
                print(f"      {line['content']}")

# Example usage
agent = SecurityReviewAgent("./my_repo")

# Perform automated security audit
critical_files = [
    "src/auth/login.py",
    "src/database/models.py", 
    "src/api/endpoints.py",
    "requirements.txt"
]

audit_report = agent.perform_security_audit(critical_files)

# Investigate specific vulnerability
agent.investigate_vulnerability("src/database/models.py", "execute(")
```

## 🎯 Advanced Use Cases

### **1. Compliance & Audit Trail**
- **SOX/SOC2 Compliance**: Track all changes to financial or customer data handling
- **GDPR Audit**: Monitor privacy-related code changes and data processing logic
- **Security Certification**: Maintain detailed change logs for security audits

### **2. Incident Response & Forensics**
- **Data Breach Investigation**: Quickly identify when and how sensitive data access was modified
- **Malicious Code Detection**: Track unauthorized changes or backdoors
- **Insider Threat Analysis**: Monitor patterns of sensitive code access by developers

### **3. Automated Vulnerability Assessment**
- **Zero-Day Discovery**: AI agents can pattern-match against known vulnerability signatures
- **Regression Testing**: Ensure security fixes don't reintroduce old vulnerabilities
- **Supply Chain Security**: Monitor third-party dependencies and integration points

### **4. Developer Security Training**
- **Learning from Mistakes**: Identify common security anti-patterns in code history
- **Best Practice Enforcement**: Highlight when secure coding practices were abandoned
- **Knowledge Transfer**: Track security expertise across team members

## 🚀 Integration with AI Security Tools

```python
# Example: Integration with AI vulnerability scanners
class AISecurityAgent:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.vulnerability_db = self.load_vulnerability_patterns()
    
    def scan_and_investigate(self, file_path):
        """AI-powered vulnerability scanning with forensic analysis"""
        
        # 1. Static analysis scan
        vulnerabilities = self.ai_vulnerability_scan(file_path)
        
        # 2. For each vulnerability found, investigate its history
        for vuln in vulnerabilities:
            print(f"🚨 Vulnerability detected: {vuln['type']} at line {vuln['line']}")
            
            # Use forensic tools to understand the vulnerability
            blame = get_file_blame(file_path)
            if blame and vuln['line'] <= len(blame['blame_lines']):
                vulnerable_line = blame['blame_lines'][vuln['line'] - 1]
                
                print(f"   Introduced by: {vulnerable_line['author']}")
                print(f"   Date: {vulnerable_line['date']}")
                print(f"   Commit: {vulnerable_line['commit_hash']}")
                
                # Get the full context of when this was added
                history = get_file_history(file_path, limit=10)
                relevant_commits = [
                    c for c in history['commits'] 
                    if c['hash'] == vulnerable_line['commit_hash']
                ]
                
                if relevant_commits:
                    commit = relevant_commits[0]
                    print(f"   Context: {commit['message']}")
                    
                    # Check if this was part of a larger security-related change
                    if any(keyword in commit['message'].lower() 
                           for keyword in ['security', 'fix', 'patch', 'vulnerability']):
                        print(f"   ⚠️  This was part of a security-related change!")
    
    def ai_vulnerability_scan(self, file_path):
        """Placeholder for AI vulnerability scanning logic"""
        # This would integrate with tools like CodeQL, Semgrep, or custom AI models
        return []
```

## 📊 Benefits for AI Agents

1. **Context-Aware Analysis**: Understand not just what code exists, but how it evolved
2. **Root Cause Analysis**: Trace vulnerabilities back to their source
3. **Pattern Recognition**: Identify recurring security issues across developers
4. **Automated Remediation**: Suggest fixes based on how similar issues were resolved
5. **Risk Assessment**: Prioritize security issues based on change frequency and author expertise
6. **Compliance Automation**: Generate audit trails and compliance reports automatically

## 🔧 Quick Start Example

```python
# Simple security audit example
from github_browser import *

# 1. Get repository info
repo_info = get_repository_info_from_git_folder(".", extract_repository_stats=True)
print(f"Auditing: {repo_info['org']}/{repo_info['repo_name']}")

# 2. Find all authentication-related files
auth_files = ["src/auth.py", "login.py", "authentication.py"]

# 3. Investigate recent changes to authentication
for auth_file in auth_files:
    print(f"\n🔐 Investigating {auth_file}")
    
    # Check recent history
    history = get_file_history(auth_file, limit=10)
    if history:
        print(f"   Recent changes: {history['total_commits']} commits")
        
        # Look for password/token related changes
        token_changes = search_file_changes(auth_file, "token")
        if token_changes['total_matches'] > 0:
            print(f"   ⚠️  {token_changes['total_matches']} token-related changes found")
            
            # Get details of the most recent change
            if token_changes['commits_with_code_changes']:
                recent_change = token_changes['commits_with_code_changes'][0]
                print(f"   Most recent: {recent_change['message']} by {recent_change['author']}")
```

This forensic analysis capability transforms AI agents from simple code scanners into sophisticated security investigators that can understand the full context and history of potential vulnerabilities. 