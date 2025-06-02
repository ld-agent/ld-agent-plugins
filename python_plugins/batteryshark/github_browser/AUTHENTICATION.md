# GitHub Browser Plugin - Enhanced Authentication Guide

The GitHub Browser plugin now supports **configurable authentication** that intelligently chooses between GitHub App and personal access token authentication based on your needs.

## 🔑 Authentication Methods

### 1. GitHub App Authentication (Organization Access)
- **Best for**: Organization repositories, team access, enterprise deployments
- **Capabilities**: Access organization repos, PRs, issues, discussions
- **Limitations**: Cannot access personal/private repositories of users
- **Setup**: Requires GitHub App installation and private key

### 2. Personal Access Token (User Access) 
- **Best for**: Personal repositories, individual development
- **Capabilities**: Access personal repos (public & private), user-owned organizations
- **Limitations**: Rate limits, requires personal token management
- **Setup**: Generate PAT with appropriate scopes

## 🚀 Quick Setup

### For Personal Repository Access
```bash
# Set your personal access token
export GITHUB_USER_TOKEN="your_personal_access_token_here"

# Prefer user authentication
export GITHUB_AUTH_PREFERENCE="user"
```

### For Organization Repository Access
```bash
# Keep existing GitHub App configuration
export GITHUB_APP_ID="your_app_id"
export GITHUB_PRIVATE_KEY_PATH="/path/to/private-key.pem"

# Prefer app authentication
export GITHUB_AUTH_PREFERENCE="app"
```

### For Mixed Usage (Recommended)
```bash
# Set both authentication methods
export GITHUB_USER_TOKEN="your_personal_access_token"
export GITHUB_APP_ID="your_app_id"
export GITHUB_PRIVATE_KEY_PATH="/path/to/private-key.pem"

# Let the system choose intelligently
export GITHUB_AUTH_PREFERENCE="auto"  # Default
```

## 📋 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_USER_TOKEN` | Personal access token for user-level operations | `ghp_xxxxxxxxxxxx` |
| `GITHUB_TOKEN` | Legacy/fallback token (app or personal) | `ghs_xxxxxxxxxxxx` |
| `GITHUB_AUTH_PREFERENCE` | Authentication preference: `app`, `user`, or `auto` | `auto` |
| `GITHUB_APP_ID` | GitHub App ID for app authentication | `1234567` |
| `GITHUB_PRIVATE_KEY_PATH` | Path to GitHub App private key file | `/path/to/key.pem` |
| `GITHUB_ORG` | Default organization name | `myorg` |
| `GITHUB_BASE_URL` | GitHub API URL (for Enterprise) | `https://api.github.com` |

## 🤖 Authentication Preferences

### `auto` (Default - Recommended)
The system intelligently chooses the best authentication method:

1. **For personal repos**: Prefers `GITHUB_USER_TOKEN`
2. **For organization repos**: Prefers GitHub App if configured
3. **Fallback logic**: Uses any available authentication

```bash
export GITHUB_AUTH_PREFERENCE="auto"
```

### `user` (Personal Access Token)
Forces use of personal access token authentication:

```bash
export GITHUB_AUTH_PREFERENCE="user"
```

### `app` (GitHub App)
Forces use of GitHub App authentication:

```bash
export GITHUB_AUTH_PREFERENCE="app"
```

## 🔍 Authentication Status

Check your current authentication status:

```python
from github_browser import get_auth_info

auth_info = get_auth_info()
print(f"Method: {auth_info['method']}")
print(f"Authenticated as: {auth_info['authenticated_as']}")
print(f"Can access private repos: {auth_info['capabilities']['can_access_private_repos']}")
```

## 🛠️ Common Use Cases

### Use Case 1: Personal Development
You want to access your personal repositories and maybe some organization repos.

```bash
# .env file
GITHUB_USER_TOKEN=ghp_your_personal_token
GITHUB_AUTH_PREFERENCE=user
```

### Use Case 2: Organization/Enterprise
You're building tools for your organization and need broad access to org repos.

```bash
# .env file
GITHUB_APP_ID=1234567
GITHUB_PRIVATE_KEY_PATH=/path/to/app-key.pem
GITHUB_ORG=myorganization
GITHUB_AUTH_PREFERENCE=app
```

### Use Case 3: Mixed Development (Recommended)
You work on both personal projects and organization projects.

```bash
# .env file
GITHUB_USER_TOKEN=ghp_your_personal_token
GITHUB_APP_ID=1234567
GITHUB_PRIVATE_KEY_PATH=/path/to/app-key.pem
GITHUB_ORG=myorganization
GITHUB_AUTH_PREFERENCE=auto
```

## 🔐 Personal Access Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token (classic) with these scopes:
   - `repo` - Full control of private repositories
   - `read:org` - Read org membership and teams
   - `read:user` - Read user profile data

3. Set the token in your environment:
```bash
export GITHUB_USER_TOKEN="ghp_your_token_here"
```

## 🏢 GitHub App Setup (for Organizations)

1. Create a GitHub App in your organization settings
2. Generate and download the private key
3. Install the app in your organization
4. Configure environment variables:

```bash
export GITHUB_APP_ID="your_app_id"
export GITHUB_PRIVATE_KEY_PATH="/path/to/private-key.pem"
```

## 🚨 Troubleshooting

### "Resource not accessible by integration" Error
- This means you're using GitHub App auth to access personal repos
- **Solution**: Set `GITHUB_AUTH_PREFERENCE=user` or add `GITHUB_USER_TOKEN`

### "Bad credentials" Error
- Your token is invalid or expired
- **Solution**: Generate a new token and update your environment

### GitHub App Authentication Failed
- Private key file not found or invalid
- App not installed in organization
- **Solution**: Check file path and app installation

### Rate Limit Issues
- Personal tokens have lower rate limits than GitHub Apps
- **Solution**: Use GitHub App for heavy API usage

## 📊 Comparison: App vs User Authentication

| Feature | GitHub App | Personal Token |
|---------|------------|----------------|
| **Rate Limit** | 5000/hour | 5000/hour |
| **Organization Repos** | ✅ Full access | ✅ If member |
| **Personal Private Repos** | ❌ No access | ✅ Full access |
| **Enterprise Features** | ✅ Full support | ⚠️ Limited |
| **Audit Logging** | ✅ Better tracking | ⚠️ Limited |
| **Token Management** | 🔄 Auto-refresh | 👤 Manual |
| **Security** | 🔒 App-scoped | 👤 User-scoped |

## 💡 Best Practices

1. **Use `auto` preference** for maximum flexibility
2. **Set both auth methods** when possible
3. **Use minimal scopes** for personal tokens
4. **Rotate tokens regularly** for security
5. **Use GitHub Apps** for production/team environments
6. **Use personal tokens** for development and personal projects

## 🔧 Testing Your Setup

Run the authentication test script:

```bash
python test_enhanced_auth.py
```

This will show your current authentication status and verify access to repositories. 