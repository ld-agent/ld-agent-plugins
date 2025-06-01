#!/usr/bin/env python3
"""
Example script showing how to use AUTOMATED authentication with SpotifyController.

This approach automatically handles the OAuth callback without requiring manual copy-pasting!
"""

import os
from controller import SpotifyController
from dotenv import load_dotenv

load_dotenv()

def main():
    # Get credentials from environment variables
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        return
    
    # Initialize controller with manual auth enabled
    controller = SpotifyController(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        manual_auth=True
    )
    
    print("🎵 Spotify Automated Authentication")
    print("=" * 40)
    print("IMPORTANT: First update your Spotify app settings!")
    print("1. Go to: https://developer.spotify.com/dashboard")
    print("2. Click on your app → Edit Settings")
    print("3. In 'Redirect URIs', add: http://127.0.0.1:8888/callback")
    print("4. Save the settings")
    print()
    print("Now let's authenticate automatically...")
    print()
    
    # Use the automated authentication method
    if controller.authenticate_automatically(timeout=120):
        print("✅ Authentication successful!")
        
        # Now you can use the controller
        print("\n🧪 Testing API calls...")
        
        # Get current playback
        current = controller.get_current_playback()
        if current:
            print(f"🎵 Currently playing: {current['track_name']} by {current['artist']}")
            if current['device']:
                print(f"📱 Device: {current['device']}")
        else:
            print("⏸️  Nothing currently playing")
        
        # Get available devices
        devices = controller.get_available_devices()
        print(f"\n📱 Available devices ({len(devices)}):")
        if devices:
            for device in devices:
                status = "🟢 Active" if device['is_active'] else "⚪ Inactive"
                volume = f" (Volume: {device['volume_percent']}%)" if device['volume_percent'] is not None else ""
                print(f"   {status} {device['name']} ({device['type']}){volume}")
        else:
            print("   No devices found. Make sure Spotify is open on at least one device.")
    
    else:
        print("❌ Authentication failed!")

if __name__ == "__main__":
    main() 