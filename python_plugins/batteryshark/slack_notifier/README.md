# Slack Notifier Plugin

Send notifications to Slack channels via webhooks.

## What it does

- Sends messages to Slack channels using webhook URLs
- Supports optional titles that appear as headers
- Supports Slack markdown formatting in messages
- Returns `True`/`False` for success/failure

## Requirements

- Python 3.10+
- `pydantic>=2.0.0`
- `requests`
- Platform: any

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_NOTIFIER_WEBHOOK_URL` | Yes | - | Your Slack webhook URL |
| `SLACK_NOTIFIER_ENABLED` | No | `true` | Enable/disable notifications |

## Setup Slack Webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App
2. Add "Incoming Webhooks" feature
3. Create webhook for desired channel
4. Set `SLACK_NOTIFIER_WEBHOOK_URL` environment variable

## Exported Functions

### Tools

#### `send_slack_notification(message, title) -> bool`
Send a notification to Slack via webhook.

**Parameters:**
- `message` (str): The main message content to send to Slack
- `title` (str, optional): Optional title for the Slack message

**Returns:** `bool` - True if message was sent successfully, False otherwise

## Usage

```python
from slack_notifier import send_slack_notification

# Basic message
send_slack_notification("Hello, Slack!")

# Message with title
send_slack_notification("Task completed successfully!", "Status Update")

# With markdown formatting
send_slack_notification("Deployment to *production* completed!", "🚀 Deploy")
``` 