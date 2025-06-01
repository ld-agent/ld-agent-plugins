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

## Security Best Practices

### Token Storage Strategy

This plugin implements different token storage strategies optimized for security in each environment:

#### Development Environment (Default)
- **Primary Storage**: File-based cache in `~/.spotify_controller.cache` 
- **Security**: File permissions set to `600` (owner read/write only)
- **Use case**: Local development and testing

#### Production Environment (Recommended)
- **Primary Storage**: Environment variables (process-scoped, ephemeral)
- **Secondary**: None! Pure environment variable storage via custom cache handler
- **Security**: Zero filesystem exposure, tokens only exist in process memory
- **Use case**: Heroku, Docker, cloud deployments, any multi-user environment

### Why Environment Variables for Production?

Environment variables are the **gold standard** for production secret storage because they're:

- ✅ **Process-scoped**: Only accessible to your process and its children
- ✅ **Ephemeral**: Automatically destroyed when process ends  
- ✅ **No filesystem exposure**: Never written to disk in plaintext
- ✅ **Restart-safe**: Perfect for cloud environments that restart frequently
- ✅ **Container-native**: Ideal for Docker, Kubernetes, serverless
- ✅ **Isolated**: Other processes can't access your tokens

**We use a custom spotipy cache handler that reads/writes directly from environment variables - no temporary files needed!**

### Environment Variables

#### Required (All Environments)
```bash
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

#### Optional Configuration
```bash
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback  # Default for development
SPOTIFY_CACHE_PATH=/custom/path/to/cache  # Custom cache location (dev only)
```

#### Production Environment
```bash
SPOTIFY_PRODUCTION_MODE=true  # Enables production token handling
SPOTIFY_ACCESS_TOKEN=your_access_token  # Pre-obtained access token
SPOTIFY_REFRESH_TOKEN=your_refresh_token  # Pre-obtained refresh token
SPOTIFY_TOKEN_EXPIRES_AT=1234567890  # Token expiration timestamp
```

### Deployment-Specific Recommendations

#### 1. Local Development
```bash
# Set basic environment variables
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"

# Plugin will use secure file-based caching
python your_app.py
```

#### 2. Docker Production
```dockerfile
FROM python:3.9
# ... your dockerfile content ...

# Set production mode
ENV SPOTIFY_PRODUCTION_MODE=true

# Tokens should be passed at runtime, not baked into image
# docker run -e SPOTIFY_ACCESS_TOKEN="..." -e SPOTIFY_REFRESH_TOKEN="..." your-app
```

#### 3. Heroku Production
```bash
# Set production mode
heroku config:set SPOTIFY_PRODUCTION_MODE=true

# Set tokens (obtain these through initial OAuth flow)
heroku config:set SPOTIFY_ACCESS_TOKEN="your_access_token"
heroku config:set SPOTIFY_REFRESH_TOKEN="your_refresh_token"
heroku config:set SPOTIFY_TOKEN_EXPIRES_AT="1234567890"
```

#### 4. Kubernetes/Cloud
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: spotify-secrets
type: Opaque
stringData:
  SPOTIFY_CLIENT_ID: "your_client_id"
  SPOTIFY_CLIENT_SECRET: "your_client_secret"
  SPOTIFY_ACCESS_TOKEN: "your_access_token"
  SPOTIFY_REFRESH_TOKEN: "your_refresh_token"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: your-app
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: SPOTIFY_PRODUCTION_MODE
          value: "true"
        envFrom:
        - secretRef:
            name: spotify-secrets
```

### Getting Production Tokens

For production deployments, you'll need to obtain tokens initially through the OAuth flow:

1. **Run locally first** to complete OAuth and get tokens:
   ```bash
   python -c "
   from spotify_controller import initialize_plugin, get_current_playback
   initialize_plugin()
   # Complete OAuth flow in browser
   "
   ```

2. **Extract tokens** from the cache file:
   ```bash
   python extract_tokens.py
   # This will output the environment variable commands
   ```

3. **Set as environment variables** in your production environment

### Clean Environment Variable Storage

In production mode, the plugin uses a custom `EnvironmentVariableCacheHandler` that integrates seamlessly with spotipy:

```python
# Production mode automatically detected
export SPOTIFY_PRODUCTION_MODE=true
export SPOTIFY_ACCESS_TOKEN="your_access_token"
export SPOTIFY_REFRESH_TOKEN="your_refresh_token"

# Your app code remains the same
from spotify_controller import get_current_playback
current = await get_current_playback()  # Uses env vars directly!
```

**No cache files, no temporary storage, just pure environment variables!**

### Security Considerations

#### ✅ Good Practices
- Use environment variables for production tokens
- Set `SPOTIFY_PRODUCTION_MODE=true` in production
- Secure your deployment environment's secret management
- Rotate tokens periodically
- Use temporary cache files with restrictive permissions

#### ❌ Avoid
- Committing cache files or tokens to version control
- Using file-based caching in shared/multi-user environments
- Storing tokens in application logs
- Using default file permissions for token storage
- Hardcoding tokens in source code

#### Additional Security Measures
- Use a secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.) for production
- Implement token rotation policies
- Monitor for unauthorized API usage
- Use least-privilege scopes when creating your Spotify app

### Troubleshooting

If you encounter authentication issues:

1. **Check environment variables**: Ensure all required variables are set
2. **Verify token expiration**: Access tokens expire after 1 hour
3. **Check file permissions**: Cache files should have `600` permissions
4. **Review logs**: The plugin logs its token storage strategy on initialization

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