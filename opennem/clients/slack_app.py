"""Slack Bot API client for interactive messages (weekly summary approval)"""

import hashlib
import hmac
import logging
import time

from fastapi import HTTPException, Request

from opennem import settings
from opennem.utils.http import http_factory

logger = logging.getLogger("opennem.clients.slack_app")

_http_client = http_factory(proxy=False, mimic_browser=False)

SLACK_API_BASE = "https://slack.com/api"


async def verify_slack_signature(request: Request) -> bytes:
    """Verify Slack request signature using HMAC-SHA256.

    Returns raw body bytes on success, raises HTTPException on failure.
    """
    if not settings.slack_signing_secret:
        raise HTTPException(status_code=500, detail="Slack signing secret not configured")

    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if not timestamp or not signature:
        raise HTTPException(status_code=403, detail="Missing Slack signature headers")

    # Reject requests older than 5 minutes (replay protection)
    if abs(time.time() - int(timestamp)) > 300:
        raise HTTPException(status_code=403, detail="Request too old")

    body = await request.body()
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    computed = (
        "v0="
        + hmac.new(
            settings.slack_signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
    )

    if not hmac.compare_digest(computed, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    return body


async def post_message_with_blocks(channel: str, blocks: list[dict], text: str = "") -> dict | None:
    """Post a message to a Slack channel using the Bot API (chat.postMessage).

    Args:
        channel: Channel ID
        blocks: Block Kit blocks (list of dicts)
        text: Fallback text for notifications

    Returns:
        Response JSON dict on success, None on failure
    """
    if not settings.slack_bot_token:
        logger.error("Slack bot token not configured")
        return None

    resp = await _http_client.post(
        f"{SLACK_API_BASE}/chat.postMessage",
        headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
        json={"channel": channel, "blocks": blocks, "text": text},
    )

    data = resp.json()
    if not data.get("ok"):
        logger.error(f"Slack chat.postMessage failed: {data.get('error')}")
        return None

    return data


async def update_message(channel: str, ts: str, blocks: list[dict] | None = None, text: str = "") -> bool:
    """Update an existing Slack message via chat.update."""
    if not settings.slack_bot_token:
        logger.error("Slack bot token not configured")
        return False

    payload: dict = {"channel": channel, "ts": ts, "text": text}
    if blocks is not None:
        payload["blocks"] = blocks

    resp = await _http_client.post(
        f"{SLACK_API_BASE}/chat.update",
        headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
        json=payload,
    )

    data = resp.json()
    if not data.get("ok"):
        logger.error(f"Slack chat.update failed: {data.get('error')}")
        return False

    return True


async def upload_image_to_slack(channel: str, image: bytes, filename: str = "summary.png", title: str = "") -> str | None:
    """Upload an image to Slack and return the public permalink.

    Uses the files.getUploadURLExternal + files.completeUploadExternal flow.
    Requires `files:write` bot scope.
    Uses raw httpx (not http_factory) to avoid wrapper interference with Slack's upload API.
    """
    import httpx

    if not settings.slack_bot_token:
        logger.error("Slack bot token not configured")
        return None

    headers = {"Authorization": f"Bearer {settings.slack_bot_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: get upload URL
        resp = await client.get(
            f"{SLACK_API_BASE}/files.getUploadURLExternal",
            headers=headers,
            params={"filename": filename, "length": len(image)},
        )
        data = resp.json()
        if not data.get("ok"):
            logger.error(f"Slack files.getUploadURLExternal failed: {data.get('error')}")
            return None

        upload_url = data["upload_url"]
        file_id = data["file_id"]

        # Step 2: upload the file bytes
        resp2 = await client.post(upload_url, content=image, headers={"Content-Type": "image/png"})
        if resp2.status_code != 200:
            logger.error(f"Slack file upload failed: {resp2.status_code}")
            return None

        # Step 3: complete the upload and share to channel
        resp3 = await client.post(
            f"{SLACK_API_BASE}/files.completeUploadExternal",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "files": [{"id": file_id, "title": title or filename}],
                "channel_id": channel,
            },
        )
        data3 = resp3.json()
        if not data3.get("ok"):
            logger.error(f"Slack files.completeUploadExternal failed: {data3.get('error')}")
            return None

        # Extract permalink from the response
        try:
            file_info = data3["files"][0]
            return file_info.get("permalink_public") or file_info.get("permalink") or file_info.get("url_private")
        except (KeyError, IndexError):
            logger.warning("Could not extract permalink from Slack upload response")
            return None


async def respond_to_interaction(response_url: str, text: str, replace_original: bool = True) -> bool:
    """Respond to a Slack interaction via the response_url (valid for 30 min, up to 5 uses)."""
    resp = await _http_client.post(
        response_url,
        json={"text": text, "replace_original": replace_original},
    )

    if resp.status_code != 200:
        logger.error(f"Slack response_url failed: {resp.status_code}: {resp.text}")
        return False

    return True


def build_weekly_summary_approval_blocks(
    summary_text: str,
    image_url: str | None,
    image_alt: str,
    callback_value: str,
) -> list[dict]:
    """Build Block Kit blocks for the weekly summary approval message.

    Args:
        summary_text: Markdown-formatted summary text
        image_url: URL of the pie chart image (from Cloudflare)
        image_alt: Alt text for the image
        callback_value: JSON string with {"network": "NEM", "week_end": "2026-03-22"} for button value

    Returns:
        List of Block Kit block dicts
    """
    blocks: list[dict] = []

    # Image block (if available)
    if image_url:
        blocks.append(
            {
                "type": "image",
                "image_url": image_url,
                "alt_text": image_alt,
            }
        )

    # Summary text block
    blocks.append(
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary_text},
        }
    )

    # Approve / Reject buttons
    blocks.append(
        {
            "type": "actions",
            "block_id": "weekly_summary_approval",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve & Publish"},
                    "style": "primary",
                    "action_id": "weekly_approve",
                    "value": callback_value,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "action_id": "weekly_reject",
                    "value": callback_value,
                },
            ],
        }
    )

    return blocks
