# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "MacOS Notifier",
    "description": "MacOS user notification functionality",
    "author": "BatteryShark",
    "version": "1.0.0",
    "platform": "macos",
    "python_requires": ">=3.10",
    "dependencies": ["pydantic>=2.0.0", "pync>=2.0.0"],
    "environment_variables": {
        "MACOS_NOTIFIER_DEFAULT_SOUND": {
            "description": "Default notification sound",
            "default": "Ping",
            "required": False
        },
        "MACOS_NOTIFIER_ENABLED": {
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
from .notifier import send_notification as _send_notification_impl

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

async def send_notification(
    message: Annotated[str, Field(description="The notification message to display")],
    title: Annotated[Optional[str], Field(description="Optional notification title", default=None)]
) -> bool:
    """
    Send a MacOS notification popup to the user.
    
    This function displays a native MacOS notification with customizable
    message and title. The notification respects system settings and can
    be disabled via environment variables.
    
    Args:
        message: The main notification message to display
        title: Optional title for the notification
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
        
    Example:
        >>> await send_notification("Hello, World!", "Test Title")
        True
    """
    return await _send_notification_impl(message, title)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [send_notification]
}
# =============================================================================
# END OF EXPORTS
# =============================================================================
