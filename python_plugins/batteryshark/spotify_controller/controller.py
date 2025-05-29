import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import webbrowser
import time
from pathlib import Path
from typing import List, Dict, Optional, Any

class SpotifyController:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://127.0.0.1:8888/callback", cache_path: str = ".cache"):
        """
        Initialize Spotify controller with your app credentials.
        
        Args:
            client_id: Your Spotify app client ID
            client_secret: Your Spotify app client secret
            redirect_uri: Redirect URI (default uses IPv4 loopback as required by Spotify)
            cache_path: Path to the token cache file
        """
        self.scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-library-read"
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.cache_path = cache_path
        
        # Ensure cache directory exists
        cache_dir = Path(cache_path).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=self.scope,
            cache_path=cache_path,
            open_browser=True  # Auto-open browser for auth
        )
        
        self.sp = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Spotify client with authentication."""
        try:
            # Try to get a cached token first
            token_info = self.auth_manager.get_cached_token()
            
            if token_info:
                # We have a cached token, create client
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                print("Spotify authentication: Using cached token")
            else:
                # No cached token, need to authenticate
                print("Spotify authentication: No cached token found, initiating OAuth flow...")
                self._perform_oauth_flow()
                
        except Exception as e:
            print(f"Error during Spotify authentication initialization: {e}")
            self.sp = None
    
    def _perform_oauth_flow(self):
        """Perform the OAuth flow to get an access token."""
        try:
            # Get authorization URL
            auth_url = self.auth_manager.get_authorize_url()
            
            print(f"Opening browser for Spotify authorization...")
            print(f"If the browser doesn't open automatically, visit: {auth_url}")
            
            # Open browser
            webbrowser.open(auth_url)
            
            # Wait for user to complete authorization
            print("Please complete the authorization in your browser...")
            print("After authorization, you'll be redirected to a localhost URL.")
            
            # Try to get token (this will handle the callback)
            token_info = self.auth_manager.get_access_token(code=None)
            
            if token_info:
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                print("Spotify authentication successful!")
            else:
                print("Failed to get access token")
                self.sp = None
                
        except Exception as e:
            print(f"Error during OAuth flow: {e}")
            print("Please check your Spotify app configuration and network connection.")
            self.sp = None
    
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        if self.sp is None:
            return False
            
        try:
            # Try to make a simple API call to verify authentication
            self.sp.current_user()
            return True
        except Exception:
            # Token might be expired, try to refresh
            try:
                token_info = self.auth_manager.get_cached_token()
                if token_info and self.auth_manager.is_token_expired(token_info):
                    print("Token expired, refreshing...")
                    token_info = self.auth_manager.refresh_access_token(token_info['refresh_token'])
                    self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                    return True
                return False
            except Exception:
                return False
    
    def _ensure_authenticated(self):
        """Ensure the client is authenticated before making API calls."""
        if not self.is_authenticated():
            print("Not authenticated. Attempting to re-authenticate...")
            self._initialize_client()
            
            if not self.is_authenticated():
                raise ValueError(
                    "Spotify authentication failed. Please check your SPOTIFY_CLIENT_ID and "
                    "SPOTIFY_CLIENT_SECRET environment variables, and ensure your Spotify app "
                    "is properly configured with the redirect URI."
                )
    
    def get_current_playback(self) -> Optional[Dict[str, Any]]:
        """Get information about the current playback state."""
        self._ensure_authenticated()
        try:
            current = self.sp.current_playback()
            if current:
                return {
                    'is_playing': current['is_playing'],
                    'track_name': current['item']['name'] if current['item'] else None,
                    'artist': ', '.join([artist['name'] for artist in current['item']['artists']]) if current['item'] else None,
                    'album': current['item']['album']['name'] if current['item'] else None,
                    'device': current['device']['name'] if current['device'] else None,
                    'progress_ms': current['progress_ms'],
                    'duration_ms': current['item']['duration_ms'] if current['item'] else None,
                    'shuffle_state': current['shuffle_state'],
                    'repeat_state': current['repeat_state']
                }
            return None
        except Exception as e:
            print(f"Error getting current playback: {e}")
            return None
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get all available Spotify devices."""
        self._ensure_authenticated()
        try:
            devices = self.sp.devices()
            return [{
                'id': device['id'],
                'name': device['name'],
                'type': device['type'],
                'is_active': device['is_active'],
                'is_private_session': device['is_private_session'],
                'is_restricted': device['is_restricted'],
                'volume_percent': device['volume_percent']
            } for device in devices['devices']]
        except Exception as e:
            print(f"Error getting devices: {e}")
            return []
    
    def transfer_playback(self, device_id: str, force_play: bool = False) -> bool:
        """Transfer playback to a specific device."""
        try:
            self.sp.transfer_playback(device_id=device_id, force_play=force_play)
            return True
        except Exception as e:
            print(f"Error transferring playback: {e}")
            return False
    
    def search_spotify(self, query: str, search_type: str = 'track', limit: int = 10) -> Dict[str, Any]:
        """
        Search Spotify for tracks, artists, albums, or playlists.
        
        Args:
            query: Search query
            search_type: 'track', 'artist', 'album', or 'playlist'
            limit: Number of results to return
        """
        try:
            results = self.sp.search(q=query, type=search_type, limit=limit)
            
            if search_type == 'track':
                return {
                    'tracks': [{
                        'id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'uri': track['uri']
                    } for track in results['tracks']['items']]
                }
            elif search_type == 'artist':
                return {
                    'artists': [{
                        'id': artist['id'],
                        'name': artist['name'],
                        'followers': artist['followers']['total'],
                        'genres': artist['genres'],
                        'uri': artist['uri']
                    } for artist in results['artists']['items']]
                }
            elif search_type == 'album':
                return {
                    'albums': [{
                        'id': album['id'],
                        'name': album['name'],
                        'artist': ', '.join([artist['name'] for artist in album['artists']]),
                        'release_date': album['release_date'],
                        'uri': album['uri']
                    } for album in results['albums']['items']]
                }
            elif search_type == 'playlist':
                return {
                    'playlists': [{
                        'id': playlist['id'],
                        'name': playlist['name'],
                        'owner': playlist['owner']['display_name'],
                        'tracks_total': playlist['tracks']['total'],
                        'uri': playlist['uri']
                    } for playlist in results['playlists']['items']]
                }
        except Exception as e:
            print(f"Error searching Spotify: {e}")
            return {}
    
    def get_user_playlists(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get current user's playlists."""
        try:
            playlists = self.sp.current_user_playlists(limit=limit)
            return [{
                'id': playlist['id'],
                'name': playlist['name'],
                'owner': playlist['owner']['display_name'],
                'tracks_total': playlist['tracks']['total'],
                'public': playlist['public'],
                'collaborative': playlist['collaborative'],
                'uri': playlist['uri']
            } for playlist in playlists['items']]
        except Exception as e:
            print(f"Error getting playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tracks from a specific playlist."""
        try:
            results = self.sp.playlist_tracks(playlist_id, limit=limit)
            tracks = []
            for item in results['items']:
                if item['track']:
                    tracks.append({
                        'id': item['track']['id'],
                        'name': item['track']['name'],
                        'artist': ', '.join([artist['name'] for artist in item['track']['artists']]),
                        'album': item['track']['album']['name'],
                        'uri': item['track']['uri'],
                        'added_at': item['added_at']
                    })
            return tracks
        except Exception as e:
            print(f"Error getting playlist tracks: {e}")
            return []
    
    def play_track(self, track_uri: str, device_id: Optional[str] = None) -> bool:
        """Play a specific track."""
        try:
            self.sp.start_playback(device_id=device_id, uris=[track_uri])
            return True
        except Exception as e:
            print(f"Error playing track: {e}")
            return False
    
    def play_playlist(self, playlist_uri: str, device_id: Optional[str] = None) -> bool:
        """Play a playlist."""
        try:
            self.sp.start_playback(device_id=device_id, context_uri=playlist_uri)
            return True
        except Exception as e:
            print(f"Error playing playlist: {e}")
            return False
    
    def play_album(self, album_uri: str, device_id: Optional[str] = None) -> bool:
        """Play an album."""
        try:
            self.sp.start_playback(device_id=device_id, context_uri=album_uri)
            return True
        except Exception as e:
            print(f"Error playing album: {e}")
            return False
    
    def pause_playback(self, device_id: Optional[str] = None) -> bool:
        """Pause current playback."""
        try:
            self.sp.pause_playback(device_id=device_id)
            return True
        except Exception as e:
            print(f"Error pausing playback: {e}")
            return False
    
    def resume_playback(self, device_id: Optional[str] = None) -> bool:
        """Resume current playback."""
        try:
            self.sp.start_playback(device_id=device_id)
            return True
        except Exception as e:
            print(f"Error resuming playback: {e}")
            return False
    
    def next_track(self, device_id: Optional[str] = None) -> bool:
        """Skip to next track."""
        try:
            self.sp.next_track(device_id=device_id)
            return True
        except Exception as e:
            print(f"Error skipping track: {e}")
            return False
    
    def previous_track(self, device_id: Optional[str] = None) -> bool:
        """Go to previous track."""
        try:
            self.sp.previous_track(device_id=device_id)
            return True
        except Exception as e:
            print(f"Error going to previous track: {e}")
            return False
    
    def set_volume(self, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """Set volume (0-100)."""
        try:
            self.sp.volume(volume_percent, device_id=device_id)
            return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False
    
    def toggle_shuffle(self, state: bool, device_id: Optional[str] = None) -> bool:
        """Toggle shuffle on/off."""
        try:
            self.sp.shuffle(state, device_id=device_id)
            return True
        except Exception as e:
            print(f"Error toggling shuffle: {e}")
            return False
    
    def set_repeat(self, state: str, device_id: Optional[str] = None) -> bool:
        """Set repeat mode: 'track', 'context', or 'off'."""
        try:
            self.sp.repeat(state, device_id=device_id)
            return True
        except Exception as e:
            print(f"Error setting repeat: {e}")
            return False

