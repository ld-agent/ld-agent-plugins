# Spotify Controller Plugin

Control Spotify playback, search music, and manage playlists through the Spotify Web API.

## What it does

- Controls Spotify playback (play, pause, skip, volume)
- Searches for tracks, artists, albums, and playlists
- Manages device playback and transfers between devices
- Accesses user playlists and music library
- Returns structured data for all operations

## Requirements

- Python 3.10+
- `spotipy>=2.22.0`
- Active Spotify account (Premium required for playback control)
- Platform: any

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPOTIFY_CLIENT_ID` | Yes | - | Your Spotify app client ID |
| `SPOTIFY_CLIENT_SECRET` | Yes | - | Your Spotify app client secret |
| `SPOTIFY_REDIRECT_URI` | No | `http://127.0.0.1:8888/callback` | OAuth redirect URI |
| `SPOTIFY_CACHE_PATH` | No | `~/.spotify_controller.cache` | Token cache file location |

## Exported Functions

### Tools

#### `get_current_playback() -> Optional[Dict[str, Any]]`
Get information about what's currently playing on Spotify.

**Returns:** Dict with track name, artist, album, device, progress, and playback state. None if nothing playing.

#### `search_spotify(query, search_type, limit) -> Dict[str, Any]`
Search Spotify for music content.

**Parameters:**
- `query` (str): Search query for tracks, artists, albums, or playlists
- `search_type` (str, optional): Type of search: 'track', 'artist', 'album', or 'playlist'
- `limit` (int, optional): Number of results to return (1-50)

**Returns:** Dict containing search results with metadata

#### `play_track(track_uri, device_id) -> bool`
Play a specific track on Spotify.

**Parameters:**
- `track_uri` (str): Spotify URI of the track (e.g., spotify:track:4iV5W9uYEdYUVa79Axb7Rh)
- `device_id` (str, optional): ID of the device to play on

**Returns:** True if successful, False otherwise

#### `play_playlist(playlist_uri, device_id) -> bool`
Play a specific playlist on Spotify.

**Parameters:**
- `playlist_uri` (str): Spotify URI of the playlist (e.g., spotify:playlist:37i9dQZF1DXcBWIGoYBM5M)
- `device_id` (str, optional): ID of the device to play on

**Returns:** True if successful, False otherwise

#### `pause_playback(device_id) -> bool`
Pause the current Spotify playback.

**Parameters:**
- `device_id` (str, optional): ID of the device to pause

**Returns:** True if successful, False otherwise

#### `resume_playback(device_id) -> bool`
Resume the current Spotify playback.

**Parameters:**
- `device_id` (str, optional): ID of the device to resume playback on

**Returns:** True if successful, False otherwise

#### `next_track(device_id) -> bool`
Skip to the next track on Spotify.

**Parameters:**
- `device_id` (str, optional): ID of the device to skip track on

**Returns:** True if successful, False otherwise

#### `previous_track(device_id) -> bool`
Go to the previous track on Spotify.

**Parameters:**
- `device_id` (str, optional): ID of the device to go to previous track on

**Returns:** True if successful, False otherwise

#### `set_volume(volume_percent, device_id) -> bool`
Set the volume for Spotify playback.

**Parameters:**
- `volume_percent` (int): Volume level from 0 to 100
- `device_id` (str, optional): ID of the device to set volume on

**Returns:** True if successful, False otherwise

#### `get_user_playlists(limit) -> List[Dict[str, Any]]`
Get the current user's Spotify playlists.

**Parameters:**
- `limit` (int, optional): Number of playlists to return (1-50)

**Returns:** List of playlists with metadata including name, owner, and track count

#### `get_available_devices() -> List[Dict[str, Any]]`
Get all available Spotify devices for playback.

**Returns:** List of devices with metadata including name, type, and status

#### `transfer_playback(device_id, force_play) -> bool`
Transfer Spotify playback to a different device.

**Parameters:**
- `device_id` (str): ID of the device to transfer playback to
- `force_play` (bool, optional): Whether to start playing immediately after transfer

**Returns:** True if successful, False otherwise

## Usage

```python
# Search for music
results = await search_spotify("Bohemian Rhapsody", "track", 5)

# Play first result
if results.get('tracks'):
    await play_track(results['tracks'][0]['uri'])

# Control playback
await pause_playback()
await set_volume(50)
await next_track()

# Get current status
current = await get_current_playback()
print(f"Playing: {current['track_name']}" if current else "Nothing playing")
```

## Setup Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create new app with redirect URI: `http://127.0.0.1:8888/callback`
3. Copy Client ID and Client Secret to environment variables
4. First use will open browser for one-time authorization 