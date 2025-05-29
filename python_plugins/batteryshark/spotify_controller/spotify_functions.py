import os
from typing import Annotated, Optional, Dict, Any, List
from pydantic import Field
from pathlib import Path
from .controller import SpotifyController

# Global controller instance
_spotify_controller = None
_initialized = False

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

def _get_controller() -> SpotifyController:
    """Get or create the Spotify controller instance."""
    global _spotify_controller
    if _spotify_controller is None:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        
        # Default cache path to user's home directory
        default_cache = str(Path.home() / ".spotify_controller.cache")
        cache_path = os.getenv("SPOTIFY_CACHE_PATH", default_cache)
        
        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables are required")
        
        _spotify_controller = SpotifyController(client_id, client_secret, redirect_uri, cache_path=cache_path)
    
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