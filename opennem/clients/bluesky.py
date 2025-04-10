"""
OpenNEM Bluesky Client
"""

import asyncio
import logging

from atproto import AsyncClient

from opennem import settings

logger = logging.getLogger("opennem.clients.bluesky")


async def post_bluesky(text: str) -> None:
    """Posts a message text to Bluesky.

    Args:
        text: The message text to post.
    """
    if not settings.bluesky_handle or not settings.bluesky_password:
        logger.error("Bluesky handle or password not configured in settings. Skipping post.")
        return

    client = AsyncClient()

    try:
        await client.login(settings.bluesky_handle, settings.bluesky_password)
        logger.info(f"Logged into Bluesky as {settings.bluesky_handle}")

        await client.send_post(text=text)
        logger.info("Successfully posted to Bluesky")

    except Exception as e:
        logger.error(f"Failed to post to Bluesky: {e}")
    finally:
        # Ensure the session is closed even if errors occur
        if client.me:
            # Check if login was successful before trying to close
            # await client.close() # Closing logic might depend on library version/implementation details
            # As of atproto 0.0.39, explicit close might not be necessary or available like this
            # The session might be managed implicitly by the client's lifecycle or context managers if used
            pass


if __name__ == "__main__":
    # Example usage for testing
    test_message = "Testing OpenNEM Bluesky integration. Hello World!"
    print(f'Attempting to post to Bluesky: "{test_message}"')
    asyncio.run(post_bluesky(test_message))
    print("Bluesky post attempt finished.")
