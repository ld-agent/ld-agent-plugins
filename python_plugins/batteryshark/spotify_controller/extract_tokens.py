#!/usr/bin/env python3
"""
Utility script to extract Spotify tokens from cache file for production deployment.

Usage:
    python extract_tokens.py [cache_file_path]

If no cache file path is provided, it will look for the default cache file.
"""

import json
import sys
from pathlib import Path
import os

def extract_tokens(cache_path=None):
    """Extract tokens from Spotify cache file for production use."""
    
    if cache_path is None:
        # Try to find default cache file
        default_cache = Path.home() / ".spotify_controller.cache"
        if default_cache.exists():
            cache_path = default_cache
        else:
            # Also check for spotipy default cache
            spotipy_cache = Path.home() / ".cache"
            if spotipy_cache.exists():
                cache_path = spotipy_cache
            else:
                print("❌ No cache file found. Please run the OAuth flow first or specify cache file path.")
                print("   Example: python extract_tokens.py ~/.cache")
                return False
    else:
        cache_path = Path(cache_path)
    
    if not cache_path.exists():
        print(f"❌ Cache file not found: {cache_path}")
        return False
    
    try:
        with open(cache_path, 'r') as f:
            token_data = json.load(f)
        
        # Extract required fields
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_at = token_data.get('expires_at', 0)
        
        if not access_token or not refresh_token:
            print("❌ Invalid token data in cache file")
            return False
        
        print("✅ Tokens extracted successfully!")
        print("\n" + "="*60)
        print("PRODUCTION ENVIRONMENT VARIABLES")
        print("="*60)
        print(f"export SPOTIFY_PRODUCTION_MODE=true")
        print(f"export SPOTIFY_ACCESS_TOKEN='{access_token}'")
        print(f"export SPOTIFY_REFRESH_TOKEN='{refresh_token}'")
        print(f"export SPOTIFY_TOKEN_EXPIRES_AT='{expires_at}'")
        print("="*60)
        
        print("\nFor Heroku deployment:")
        print(f"heroku config:set SPOTIFY_PRODUCTION_MODE=true")
        print(f"heroku config:set SPOTIFY_ACCESS_TOKEN='{access_token}'")
        print(f"heroku config:set SPOTIFY_REFRESH_TOKEN='{refresh_token}'")
        print(f"heroku config:set SPOTIFY_TOKEN_EXPIRES_AT='{expires_at}'")
        
        print("\nFor Docker deployment:")
        print("Add these to your docker run command:")
        print(f"  -e SPOTIFY_PRODUCTION_MODE=true \\")
        print(f"  -e SPOTIFY_ACCESS_TOKEN='{access_token}' \\")
        print(f"  -e SPOTIFY_REFRESH_TOKEN='{refresh_token}' \\")
        print(f"  -e SPOTIFY_TOKEN_EXPIRES_AT='{expires_at}'")
        
        print("\n⚠️  SECURITY REMINDER:")
        print("   - Never commit these tokens to version control")
        print("   - Store them securely in your deployment environment")
        print("   - Rotate tokens periodically")
        print("   - Use your cloud provider's secret management service")
        
        return True
        
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in cache file: {cache_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading cache file: {e}")
        return False

def main():
    """Main function."""
    cache_path = None
    if len(sys.argv) > 1:
        cache_path = sys.argv[1]
    
    success = extract_tokens(cache_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 