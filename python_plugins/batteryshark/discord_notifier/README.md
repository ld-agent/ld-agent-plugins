# Discord Notifier Plugin

Send notifications to Discord channels via webhooks.

## What it does

- Sends messages to Discord channels using webhook URLs
- Supports custom titles and bot names
- Returns `True`/`False` for success/failure

## Requirements

- Python 3.10+
- `pydantic>=2.0.0`
- `requests`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_NOTIFIER_WEBHOOK_URL` | Yes | - | Your Discord webhook URL |
| `DISCORD_NOTIFIER_ENABLED` | No | `true` | Enable/disable notifications |
| `DISCORD_NOTIFIER_BOT_NAME` | No | `MCP Helper` | Bot name in Discord |

## Exported Functions

### Tools

#### `send_discord_notification(message, title, bot_name) -> bool`
Send a notification message to Discord via webhook.

**Parameters:**
- `message` (str): The message content to send to Discord
- `title` (str, optional): Optional title for the Discord embed  
- `bot_name` (str, optional): Optional bot name to display as sender

**Returns:** `bool` - True if message was sent successfully, False otherwise

## Usage

```python
from discord_notifier import send_discord_notification

# Simple message
send_discord_notification("Hello Discord!")

# With title
send_discord_notification("Deployment complete!", title="🚀 Status")

# Custom bot name
send_discord_notification("Alert!", title="⚠️ Warning", bot_name="Monitor")
```

## Setup Discord Webhook

1. Go to your Discord server → Settings → Integrations → Webhooks
2. Create new webhook, copy the URL
3. Set `DISCORD_NOTIFIER_WEBHOOK_URL` environment variable 