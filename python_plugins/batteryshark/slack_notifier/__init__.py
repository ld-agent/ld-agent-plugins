# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Slack Notifier",
    "description": "Slack Webhook notification functionality",
    "author": "BatteryShark",
    "version": "1.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": ["pydantic>=2.0.0", "requests"],
    "environment_variables": {
        "SLACK_NOTIFIER_WEBHOOK_URL": {
            "description": "Slack Webhook URL",
            "default": "",
            "required": True
        },
        "SLACK_NOTIFIER_ENABLED": {
            "description": "Enable/disable notifications",
            "default": "true",
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
from .notifier import send_slack_notification as _send_slack_notification_impl

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

def send_slack_notification(
    message: Annotated[str, Field(description="The main message content to send to Slack")],
    title: Annotated[Optional[str], Field(description="Optional title for the Slack message", default="")]
) -> bool:
    """
    Send a notification to Slack via webhook.
    
    This function sends messages to a Slack channel using a configured webhook URL.
    Messages support Slack markdown formatting and can include optional titles
    that appear as headers in the Slack message.
    
    Args:
        message: The main message content to send to Slack
        title: Optional title that appears as a header in the Slack message
    
    Returns:
        bool: True if message was sent successfully, False otherwise
        
    Example:
        >>> send_slack_notification("Hello, Slack!")
        True
        >>> send_slack_notification("Task completed", "Status Update")
        True
    """
    return _send_slack_notification_impl(message, title)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [send_slack_notification]
}
# =============================================================================
# END OF EXPORTS
# ============================================================================= 