"""
OpenNEM Bluesky Client

Supports two accounts:
- Main (bluesky_handle) — weekly summaries, general posts
- Records (bluesky_records_handle) — milestone/record posts
"""

import asyncio
import io
import logging

from atproto import AsyncClient

from opennem import settings

logger = logging.getLogger("opennem.clients.bluesky")


def _get_credentials(account: str = "main") -> tuple[str | None, str | None]:
    """Get Bluesky credentials for the specified account."""
    if account == "records":
        return settings.bluesky_records_handle, settings.bluesky_records_password
    return settings.bluesky_handle, settings.bluesky_password


async def post_bluesky(text: str, account: str = "main") -> None:
    """Posts a message text to Bluesky."""
    handle, password = _get_credentials(account)
    if not handle or not password:
        logger.error(f"Bluesky {account} account not configured. Skipping post.")
        return

    client = AsyncClient()

    try:
        await client.login(handle, password)
        logger.info(f"Logged into Bluesky as {handle}")

        await client.send_post(text=text)
        logger.info("Successfully posted to Bluesky")

    except Exception as e:
        logger.error(f"Failed to post to Bluesky: {e}")
        raise


async def post_bluesky_with_image(text: str, image: io.BytesIO, alt_text: str = "", account: str = "main") -> None:
    """Posts a message with an image to Bluesky."""
    handle, password = _get_credentials(account)
    if not handle or not password:
        logger.error(f"Bluesky {account} account not configured. Skipping post.")
        return

    client = AsyncClient()

    try:
        await client.login(handle, password)
        logger.info(f"Logged into Bluesky as {handle}")

        image.seek(0)
        image_data = image.read()
        blob_resp = await client.upload_blob(image_data)

        embed = {
            "$type": "app.bsky.embed.images",
            "images": [{"alt": alt_text, "image": blob_resp.blob}],
        }

        await client.send_post(text=text, embed=embed)
        logger.info("Successfully posted to Bluesky with image")

    except Exception as e:
        logger.error(f"Failed to post to Bluesky with image: {e}")
        raise


if __name__ == "__main__":
    test_message = "Testing OpenNEM Bluesky integration. Hello World!"
    print(f'Attempting to post to Bluesky: "{test_message}"')
    asyncio.run(post_bluesky(test_message))
    print("Bluesky post attempt finished.")
