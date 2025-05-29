import requests
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_discord_notification(message: str, title: str = "", bot_name: Optional[str] = None) -> bool:
    """
    Implementation function for send_discord_notification.
    
    Sends a Discord notification via webhook with proper error handling.
    
    Args:
        message: The message content to send
        title: Optional title for the embed
        bot_name: Optional bot name (uses environment default if None)
    
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        # Validate inputs
        if not message or not isinstance(message, str):
            logger.error("Invalid message parameter: message must be a non-empty string")
            return False
        
        # Check if notifications are enabled
        if os.getenv("DISCORD_NOTIFIER_ENABLED", "true").lower() == "false":
            logger.info("Discord notifications are disabled")
            return False
        
        # Get webhook URL
        webhook_url = os.getenv("DISCORD_NOTIFIER_WEBHOOK_URL")
        if not webhook_url:
            logger.error("DISCORD_NOTIFIER_WEBHOOK_URL environment variable not set")
            return False
        
        # Use provided bot_name or fallback to environment variable
        if bot_name is None:
            bot_name = os.getenv("DISCORD_NOTIFIER_BOT_NAME", "MCP Helper")
        
        # Prepare Discord embed
        embed = {
            "title": title,
            "description": message,
            "color": 10181046
        }

        data = {
            "username": bot_name,
            "embeds": [embed]
        }

        # Send the request
        response = requests.post(webhook_url, json=data, timeout=10)

        if response.status_code != 204:
            logger.error(f'Discord webhook returned status code {response.status_code}: {response.text}')
            return False
        
        logger.info('Message sent to Discord webhook successfully')
        return True
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error when sending Discord notification: {str(e)}")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error when sending Discord notification: {str(e)}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error when sending Discord notification: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in {__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    send_discord_notification("Hello, world!")