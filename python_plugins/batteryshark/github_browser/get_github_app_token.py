#!/usr/bin/env python3
"""
Simple GitHub App Token Generator

This script generates GitHub App installation tokens using your app's private key.
Installation tokens are what you use to authenticate API calls as your GitHub App.

Usage:
    python3 get_github_app_token.py

Requirements:
    - GITHUB_APP_ID environment variable with your App ID
    - Private key file in the same directory
    - PyJWT library: pip install PyJWT cryptography
"""

import os
import sys
import time
import jwt
import requests
import urllib3
from dotenv import load_dotenv

# Load environment variables and disable SSL warnings
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_github_app_token(app_id, private_key_path, github_base_url="https://github.com"):
    """
    Get GitHub App installation token.
    
    Args:
        app_id: Your GitHub App ID (found in app settings)
        private_key_path: Path to your private key .pem file
        github_base_url: GitHub Enterprise base URL
    
    Returns:
        Installation access token string
    """
    
    # Step 1: Read the private key
    try:
        with open(private_key_path, 'r') as f:
            private_key = f.read()
    except Exception as e:
        raise Exception(f"❌ Failed to read private key: {e}")
    
    # Step 2: Create JWT token
    try:
        payload = {
            'iat': int(time.time()),  # Issued at time
            'exp': int(time.time()) + (10 * 60),  # Expires in 10 minutes
            'iss': app_id  # GitHub App ID
        }
        
        jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
    except Exception as e:
        raise Exception(f"❌ Failed to generate JWT: {e}")
    
    # Step 3: Get installations
    try:
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(
            f"{github_base_url}/api/v3/app/installations",
            headers=headers,
            verify=False
        )
        
        if response.status_code != 200:
            raise Exception(f"❌ Failed to get installations: {response.status_code} - {response.text}")
        
        installations = response.json()
        
    except Exception as e:
        raise Exception(f"❌ Error getting installations: {e}")
    
    # Step 4: Get installation token for first installation
    if not installations:
        raise Exception("❌ No installations found. Make sure your GitHub App is installed in an organization.")
    
    installation_id = installations[0]['id']
    org_name = installations[0]['account']['login']
    
    try:
        response = requests.post(
            f"{github_base_url}/api/v3/app/installations/{installation_id}/access_tokens",
            headers=headers,
            verify=False
        )
        
        if response.status_code != 201:
            raise Exception(f"❌ Failed to get installation token: {response.status_code} - {response.text}")
        
        token = response.json()['token']
        
        print(f"✅ Successfully got GitHub App token for '{org_name}' organization")
        return token
        
    except Exception as e:
        raise Exception(f"❌ Error getting installation token: {e}")

def save_token_to_env(token):
    """Save token to .env file."""
    try:
        env_file = '.env'
        lines = []
        
        # Read existing .env if it exists
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # Remove any existing GITHUB_TOKEN line
        lines = [line for line in lines if not line.startswith('GITHUB_TOKEN=')]
        
        # Add new token
        lines.append(f'GITHUB_TOKEN={token}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"💾 Token saved to {env_file}")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not save token to .env: {e}")
        print(f"📝 Please manually add this to your .env file:")
        print(f"GITHUB_TOKEN={token}")
        return False

def main():
    """Main function."""
    print("🔐 GitHub App Token Generator")
    print("=" * 40)
    
    # Get configuration
    app_id = os.getenv('GITHUB_APP_ID')
    if not app_id:
        print("❌ Error: GITHUB_APP_ID environment variable not set")
        print("   Please set it to your GitHub App ID (found in your app settings)")
        print("   Example: export GITHUB_APP_ID=123")
        return
    
    private_key_path = None
    if len(sys.argv) > 1:
        private_key_path = sys.argv[1]

    # Look for private key file only if one was not specified at command line
    if not private_key_path:
        private_key_files = [f for f in os.listdir('.') if f.endswith('.private-key.pem')]
    else:
        private_key_files = [private_key_path]
    
    if not private_key_files:
        print("❌ Error: No private key file found")
        print("   Please put your GitHub App private key (.pem file) in this directory")
        return
    
    private_key_path = private_key_files[0]
    print(f"📋 Using App ID: {app_id}")
    print(f"🔑 Using private key: {private_key_path}")
    
    try:
        # Get the token
        token = get_github_app_token(app_id, private_key_path)
        
        # Save to .env file
        save_token_to_env(token)
        
        # Set in current environment
        os.environ['GITHUB_TOKEN'] = token
        
        print("\n🎉 Success! Your GitHub App token is ready to use.")
        print("   The token has been saved to .env and is available as GITHUB_TOKEN")
        
    except Exception as e:
        print(f"\n{e}")

if __name__ == "__main__":
    main() 