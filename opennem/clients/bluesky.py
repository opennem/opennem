"""
OpenNEM Bluesky Client

Supports two accounts:
- Main (bluesky_handle) — weekly summaries, general posts
- Records (bluesky_records_handle) — milestone/record posts

All publish functions return a dict: {"platform_post_id": atproto_uri, "permalink": web_url, "cid": cid}
"""

import asyncio
import io
import logging

from atproto import AsyncClient
from atproto_client.models.app.bsky.feed.post import ReplyRef
from atproto_client.models.com.atproto.repo.strong_ref import Main as StrongRef

from opennem import settings

logger = logging.getLogger("opennem.clients.bluesky")


def _get_credentials(account: str = "main") -> tuple[str | None, str | None]:
    """Get Bluesky credentials for the specified account."""
    if account == "records":
        return settings.bluesky_records_handle, settings.bluesky_records_password
    return settings.bluesky_handle, settings.bluesky_password


def _at_uri_to_permalink(uri: str | None, handle: str | None) -> str | None:
    """Turn at://did:plc:.../app.bsky.feed.post/<rkey> into a https://bsky.app URL."""
    if not uri or not handle:
        return None
    try:
        rkey = uri.rsplit("/", 1)[-1]
        return f"https://bsky.app/profile/{handle}/post/{rkey}"
    except Exception:
        return None


def _build_result(resp, handle: str | None) -> dict:
    uri = getattr(resp, "uri", None)
    cid = getattr(resp, "cid", None)
    return {
        "platform_post_id": uri,
        "permalink": _at_uri_to_permalink(uri, handle),
        "cid": cid,
    }


async def post_bluesky(text: str, account: str = "main") -> dict:
    """Posts a message text to Bluesky. Returns {platform_post_id, permalink, cid}."""
    handle, password = _get_credentials(account)
    if not handle or not password:
        logger.error(f"Bluesky {account} account not configured. Skipping post.")
        return {}

    client = AsyncClient()

    try:
        await client.login(handle, password)
        logger.info(f"Logged into Bluesky as {handle}")

        resp = await client.send_post(text=text)
        logger.info("Successfully posted to Bluesky")
        return _build_result(resp, handle)

    except Exception as e:
        logger.error(f"Failed to post to Bluesky: {e}")
        raise


async def post_bluesky_with_image(text: str, image: io.BytesIO, alt_text: str = "", account: str = "main") -> dict:
    """Posts a message with an image to Bluesky. Returns {platform_post_id, permalink, cid}."""
    handle, password = _get_credentials(account)
    if not handle or not password:
        logger.error(f"Bluesky {account} account not configured. Skipping post.")
        return {}

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

        resp = await client.send_post(text=text, embed=embed)
        logger.info("Successfully posted to Bluesky with image")
        return _build_result(resp, handle)

    except Exception as e:
        logger.error(f"Failed to post to Bluesky with image: {e}")
        raise


async def post_bluesky_reply(
    text: str,
    parent_uri: str,
    parent_cid: str,
    root_uri: str | None = None,
    root_cid: str | None = None,
    account: str = "main",
) -> dict:
    """Post a reply on Bluesky. AT requires both `root` and `parent` strong refs;
    for a first-level reply, root and parent are the same post.
    Returns {platform_post_id, permalink, cid}."""
    handle, password = _get_credentials(account)
    if not handle or not password:
        logger.error(f"Bluesky {account} account not configured. Skipping reply.")
        return {}

    client = AsyncClient()

    try:
        await client.login(handle, password)

        parent_ref = StrongRef(uri=parent_uri, cid=parent_cid)
        root_ref = StrongRef(uri=root_uri or parent_uri, cid=root_cid or parent_cid)
        reply_ref = ReplyRef(parent=parent_ref, root=root_ref)

        resp = await client.send_post(text=text, reply_to=reply_ref)
        logger.info("Successfully posted Bluesky reply")
        return _build_result(resp, handle)

    except Exception as e:
        logger.error(f"Failed to post Bluesky reply: {e}")
        raise


if __name__ == "__main__":
    test_message = "Testing OpenNEM Bluesky integration. Hello World!"
    print(f'Attempting to post to Bluesky: "{test_message}"')
    asyncio.run(post_bluesky(test_message))
    print("Bluesky post attempt finished.")
