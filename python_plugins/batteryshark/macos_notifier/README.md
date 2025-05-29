# MacOS Notifier Plugin

Send native macOS notification popups to the user.

## What it does

- Displays native macOS notifications with custom messages and titles
- Respects system notification settings and preferences
- Can be disabled via environment variables
- Returns `True`/`False` for success/failure

## Requirements

- Python 3.10+
- `pydantic>=2.0.0`
- `pync>=2.0.0`
- Platform: macOS

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MACOS_NOTIFIER_ENABLED` | No | `true` | Enable/disable notifications |
| `MACOS_NOTIFIER_DEFAULT_SOUND` | No | `Ping` | Default notification sound |

### Available Sounds
Common macOS notification sounds include:
- `Ping` (default)
- `Pop`
- `Blow`
- `Bottle`
- `Frog`
- `Funk`
- `Glass`
- `Hero`
- `Morse`
- `Purr`
- `Sosumi`
- `Submarine`
- `Tink`

## Exported Functions

### Tools

#### `send_notification(message, title) -> bool`
Send a MacOS notification popup to the user.

**Parameters:**
- `message` (str): The notification message to display
- `title` (str, optional): Optional notification title

**Returns:** `bool` - True if notification was sent successfully, False otherwise

## Usage

```python
from macos_notifier import send_notification

# Basic notification
await send_notification("Hello, World!")

# Notification with title
await send_notification("Task completed", "Success")
``` 