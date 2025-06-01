import os
from typing import Annotated, Optional, Dict, Any, List
from pydantic import Field
from pathlib import Path
from .controller import SpotifyController
import stat
import json
import tempfile

# Global controller instance
_spotify_controller = None
_initialized = False


class EnvironmentVariableCacheHandler:
    """
    A spotipy cache handler that stores tokens in environment variables.
    Perfect for production environments where you want process-scoped, ephemeral token storage.
    """
    
    def __init__(self, access_token_env="SPOTIFY_ACCESS_TOKEN", 
                 refresh_token_env="SPOTIFY_REFRESH_TOKEN",
                 expires_at_env="SPOTIFY_TOKEN_EXPIRES_AT"):
        """
        Initialize the environment variable cache handler.
        
        Args:
            access_token_env: Environment variable name for access token
            refresh_token_env: Environment variable name for refresh token  
            expires_at_env: Environment variable name for token expiration timestamp
        """
        self.access_token_env = access_token_env
        self.refresh_token_env = refresh_token_env
        self.expires_at_env = expires_at_env
    
    def get_cached_token(self):
        """Get token info from environment variables."""
        access_token = os.getenv(self.access_token_env)
        refresh_token = os.getenv(self.refresh_token_env)
        expires_at = os.getenv(self.expires_at_env, "0")
        
        if not access_token or not refresh_token:
            return None
            
        try:
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_at": int(expires_at),
                "scope": os.getenv("SPOTIFY_SCOPE", "")
            }
        except ValueError:
            # Invalid expires_at timestamp
            return None
    
    def save_token_to_cache(self, token_info):
        """
        Save token info to environment variables.
        
        Note: This only works if the process has permission to modify its environment.
        In most production environments, you'll set these externally via your deployment platform.
        """
        if not token_info:
            return
            
        # Update environment variables for current process
        # (This won't persist beyond the current process, which is exactly what we want!)
        os.environ[self.access_token_env] = token_info.get("access_token", "")
        os.environ[self.refresh_token_env] = token_info.get("refresh_token", "")
        os.environ[self.expires_at_env] = str(token_info.get("expires_at", 0))
        
        if "scope" in token_info:
            os.environ["SPOTIFY_SCOPE"] = token_info["scope"]


def initialize_plugin():
    """
    Initialize the Spotify Controller plugin with current environment variables.
    This should be called by agentkit after environment setup.
    Ensures proper OAuth authentication and token caching.
    """
    global _initialized, _spotify_controller
    _initialized = False  # Force re-initialization
    _spotify_controller = None  # Reset controller
    _ensure_initialized()
    print("Spotify Controller Plugin initialized")

def _ensure_initialized():
    """Ensure the plugin is properly initialized."""
    global _initialized
    if not _initialized:
        _get_controller()  # This will trigger initialization
        _initialized = True

def reset_controller():
    """Reset the global controller instance."""
    global _spotify_controller
    _spotify_controller = None

def _secure_cache_file(cache_path: str):
    """Ensure cache file has secure permissions (600 - owner read/write only)."""
    cache_file = Path(cache_path)
    if cache_file.exists():
        # Set permissions to owner read/write only
        cache_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

def _get_cache_strategy():
    """Determine the appropriate cache strategy based on environment."""
    # Check if we're in a production environment
    is_production = os.getenv("SPOTIFY_PRODUCTION_MODE", "false").lower() == "true"
    
    if is_production or os.getenv("SPOTIFY_ACCESS_TOKEN"):
        # Production: Use environment variables
        return "environment"
    else:
        # Development: Use file-based cache
        return "file"

def _create_secure_temp_cache():
    """Create a secure temporary cache file for production environments."""
    # Create a temporary file with secure permissions
    fd, temp_path = tempfile.mkstemp(prefix="spotify_cache_", suffix=".json")
    os.close(fd)  # Close the file descriptor
    
    # Set secure permissions
    os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)
    
    return temp_path

def _get_controller() -> SpotifyController:
    """Get or create the Spotify controller instance."""
    global _spotify_controller
    if _spotify_controller is None:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        
        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables are required")
        
        cache_strategy = _get_cache_strategy()
        
        if cache_strategy == "environment":
            # PRODUCTION: Use environment variable cache handler (pure environment variables!)
            print("🔒 Production mode: Using environment variable token storage (process-scoped, zero filesystem exposure)")
            
            # Create controller with custom environment variable cache handler
            from spotipy.oauth2 import SpotifyOAuth
            import spotipy
            
            # Create the OAuth manager with our custom cache handler
            cache_handler = EnvironmentVariableCacheHandler()
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-library-read",
                cache_handler=cache_handler,
                open_browser=False  # Don't auto-open browser in production
            )
            
            # Create a minimal SpotifyController that uses our auth manager
            _spotify_controller = SpotifyController(client_id, client_secret, redirect_uri, manual_auth=True)
            _spotify_controller.auth_manager = auth_manager
            _spotify_controller.sp = spotipy.Spotify(auth_manager=auth_manager)
            
        else:
            # DEVELOPMENT: File-based cache for convenience
            default_cache = str(Path.home() / ".spotify_controller.cache")
            cache_path = os.getenv("SPOTIFY_CACHE_PATH", default_cache)
            print(f"🛠️  Development mode: File-based cache at {cache_path}")
            
            _spotify_controller = SpotifyController(client_id, client_secret, redirect_uri, cache_path=cache_path)
            _secure_cache_file(cache_path)
    
    return _spotify_controller

async def get_current_playback() -> Optional[Dict[str, Any]]:
    """
    Get information about what's currently playing on Spotify.
    
    Args:
        None
    
    Returns:
        Optional[Dict[str, Any]]: Current playback information including track name, artist, 
        album, device, progress, and playback state. None if nothing is playing.
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.get_current_playback()

async def search_spotify(
    query: Annotated[str, Field(description="Search query for tracks, artists, albums, or playlists")],
    search_type: Annotated[str, Field(description="Type of search: 'track', 'artist', 'album', or 'playlist'")] = "track",
    limit: Annotated[int, Field(description="Number of results to return (1-50)", ge=1, le=50)] = 10
) -> Dict[str, Any]:
    """
    Search Spotify for music content.
    
    Args:
        query: Search query for tracks, artists, albums, or playlists
        search_type: Type of search: 'track', 'artist', 'album', or 'playlist'
        limit: Number of results to return (1-50)
        
    Returns:
        Dict[str, Any]: Search results containing list of found items with metadata
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.search_spotify(query, search_type, limit)

async def play_track(
    track_uri: Annotated[str, Field(description="Spotify URI of the track to play (e.g., spotify:track:4iV5W9uYEdYUVa79Axb7Rh)")],
    device_id: Annotated[Optional[str], Field(description="ID of the device to play on (optional)")] = None
) -> bool:
    """
    Play a specific track on Spotify.
    
    Args:
        track_uri: Spotify URI of the track to play (e.g., spotify:track:4iV5W9uYEdYUVa79Axb7Rh)
        device_id: ID of the device to play on (optional)
        
    Returns:
        bool: True if track started playing successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.play_track(track_uri, device_id)

async def play_playlist(
    playlist_uri: Annotated[str, Field(description="Spotify URI of the playlist to play (e.g., spotify:playlist:37i9dQZF1DXcBWIGoYBM5M)")],
    device_id: Annotated[Optional[str], Field(description="ID of the device to play on (optional)")] = None
) -> bool:
    """
    Play a specific playlist on Spotify.
    
    Args:
        playlist_uri: Spotify URI of the playlist to play (e.g., spotify:playlist:37i9dQZF1DXcBWIGoYBM5M)
        device_id: ID of the device to play on (optional)
        
    Returns:
        bool: True if playlist started playing successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.play_playlist(playlist_uri, device_id)

async def pause_playback(
    device_id: Annotated[Optional[str], Field(description="ID of the device to pause (optional)")] = None
) -> bool:
    """
    Pause the current Spotify playback.
    
    Args:
        device_id: ID of the device to pause (optional)
        
    Returns:
        bool: True if playback paused successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.pause_playback(device_id)

async def resume_playback(
    device_id: Annotated[Optional[str], Field(description="ID of the device to resume playback on (optional)")] = None
) -> bool:
    """
    Resume the current Spotify playback.
    
    Args:
        device_id: ID of the device to resume playback on (optional)
        
    Returns:
        bool: True if playback resumed successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.resume_playback(device_id)

async def next_track(
    device_id: Annotated[Optional[str], Field(description="ID of the device to skip track on (optional)")] = None
) -> bool:
    """
    Skip to the next track on Spotify.
    
    Args:
        device_id: ID of the device to skip track on (optional)
        
    Returns:
        bool: True if skipped to next track successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.next_track(device_id)

async def previous_track(
    device_id: Annotated[Optional[str], Field(description="ID of the device to go to previous track on (optional)")] = None
) -> bool:
    """
    Go to the previous track on Spotify.
    
    Args:
        device_id: ID of the device to go to previous track on (optional)
        
    Returns:
        bool: True if went to previous track successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.previous_track(device_id)

async def set_volume(
    volume_percent: Annotated[int, Field(description="Volume level from 0 to 100", ge=0, le=100)],
    device_id: Annotated[Optional[str], Field(description="ID of the device to set volume on (optional)")] = None
) -> bool:
    """
    Set the volume for Spotify playback.
    
    Args:
        volume_percent: Volume level from 0 to 100
        device_id: ID of the device to set volume on (optional)
        
    Returns:
        bool: True if volume set successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.set_volume(volume_percent, device_id)

async def get_user_playlists(
    limit: Annotated[int, Field(description="Number of playlists to return (1-50)", ge=1, le=50)] = 20
) -> List[Dict[str, Any]]:
    """
    Get the current user's Spotify playlists.
    
    Args:
        limit: Number of playlists to return (1-50)
        
    Returns:
        List[Dict[str, Any]]: List of user's playlists with metadata including name, owner, and track count
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.get_user_playlists(limit)

async def get_available_devices() -> List[Dict[str, Any]]:
    """
    Get all available Spotify devices for playback.
    
    Args:
        None
    
    Returns:
        List[Dict[str, Any]]: List of available devices with metadata including name, type, and status
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.get_available_devices()

async def transfer_playback(
    device_id: Annotated[str, Field(description="ID of the device to transfer playback to")],
    force_play: Annotated[bool, Field(description="Whether to start playing immediately after transfer")] = False
) -> bool:
    """
    Transfer Spotify playback to a different device.
    
    Args:
        device_id: ID of the device to transfer playback to
        force_play: Whether to start playing immediately after transfer
        
    Returns:
        bool: True if playback transferred successfully, False otherwise
    """
    _ensure_initialized()
    controller = _get_controller()
    return controller.transfer_playback(device_id, force_play) 