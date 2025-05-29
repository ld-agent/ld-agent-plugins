import os
from typing import Annotated
from pydantic import Field

import pync


async def send_notification(
        message: Annotated[str, Field(description="The notification message")],
        title: Annotated[str, Field(description="Optional notification title")] = None
) -> bool:
    """Send a MacOS notification popup to the user."""
    # Check if notifications are enabled
    if os.getenv("MACOS_NOTIFIER_ENABLED", "true").lower() == "false":
        print("MacOS notifications are disabled")
        return False
    
    try:
        sound = os.getenv("MACOS_NOTIFIER_DEFAULT_SOUND", "Ping")
        pync.notify(message, title=title, sound=sound)
        return True
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False

if __name__ == "__main__":
    import asyncio

    print("Testing notification function directly...")
    asyncio.run(send_notification("Hello, World!", "Test Title"))