"""
Discord Notifier Plugin

This plugin provides Discord webhook notification functionality for sending
messages and alerts to Discord channels through webhooks.
"""

# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Discord Notifier",
    "description": "Discord Webhook notification functionality",
    "author": "BatteryShark",
    "version": "1.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": ["pydantic>=2.0.0", "requests"],
    "environment_variables": {
        "DISCORD_NOTIFIER_WEBHOOK_URL": {
            "description": "Discord Webhook URL",
            "default": "",
            "required": True
        },
        "DISCORD_NOTIFIER_ENABLED": {
            "description": "Enable/disable notifications",
            "default": "true",
            "required": False
        },
        "DISCORD_NOTIFIER_BOT_NAME": {
            "description": "Bot name",
            "default": "MCP Helper",
            "required": False
        }
    }
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

from typing import Annotated, Optional
from pydantic import Field

# Import implementation function
from .notifier import send_discord_notification as _send_discord_notification_impl

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

def send_discord_notification(
    message: Annotated[str, Field(description="The message content to send to Discord")],
    title: Annotated[Optional[str], Field(description="Optional title for the Discord embed", default="")],
    bot_name: Annotated[Optional[str], Field(description="Optional bot name to display as sender", default=None)]
) -> bool:
    """
    Send a notification message to Discord via webhook.
    
    This function sends a message to a Discord channel using a webhook URL.
    The message is formatted as a Discord embed with optional title and custom bot name.
    
    Args:
        message: The message content to send to Discord
        title: Optional title for the Discord embed
        bot_name: Optional bot name to display as sender (uses environment default if None)
    
    Returns:
        bool: True if message was sent successfully, False otherwise
        
    Raises:
        ValueError: When webhook URL is not configured
        ConnectionError: When Discord webhook is unreachable
        
    Example:
        >>> success = send_discord_notification("Hello Discord!", "Test Message")
        >>> print(success)
        True
    """
    return _send_discord_notification_impl(message, title, bot_name)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [send_discord_notification]
}
# =============================================================================
# END OF EXPORTS
# =============================================================================
