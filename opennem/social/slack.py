"""Slack integration for the social media pipeline.

Handles sending approval requests, updating post status,
and posting publish results as thread replies.
"""

import logging
from uuid import UUID

from opennem import settings
from opennem.clients.slack_app import (
    build_weekly_summary_approval_blocks,
    post_message_with_blocks,
    upload_image_to_slack,
)
from opennem.db import get_read_session
from opennem.db.models.opennem import SocialPost

logger = logging.getLogger("opennem.social.slack")


async def send_approval_request(
    post_id: UUID,
    text_content: str,
    image: bytes | None = None,
) -> tuple[str | None, str | None]:
    """Post approval message to Slack with Approve/Reject buttons.

    Returns (channel_id, message_ts) for later updates.
    """
    channel = settings.slack_weekly_summary_channel
    if not channel:
        logger.warning("slack_weekly_summary_channel not configured")
        return None, None

    # Upload image if provided
    if image:
        await upload_image_to_slack(
            channel=channel,
            image=image,
            filename=f"social_post_{post_id}.png",
            title="Social media post preview",
        )

    # Build approval blocks — callback_value is the post UUID
    callback_value = str(post_id)
    truncated = text_content[:200] + "..." if len(text_content) > 200 else text_content
    blocks = build_weekly_summary_approval_blocks(
        summary_text=truncated,
        image_url=None,  # image uploaded separately as file
        image_alt="Social media post",
        callback_value=callback_value,
    )

    result = await post_message_with_blocks(
        channel=channel,
        blocks=blocks,
        text="Social post ready for approval",
    )

    if result:
        return result.get("channel"), result.get("ts")

    return None, None


async def update_post_status_in_slack(post_id: UUID, message: str) -> None:
    """Update the original Slack approval message with a status update."""
    import httpx

    async with get_read_session() as session:
        post = await session.get(SocialPost, post_id)
        if not post or not post.slack_channel_id or not post.slack_message_ts:
            return

        channel = post.slack_channel_id
        ts = post.slack_message_ts

    if not settings.slack_bot_token:
        return

    # Update the original message text (remove buttons)
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://slack.com/api/chat.update",
            headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
            json={
                "channel": channel,
                "ts": ts,
                "text": message,
                "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": message}}],
            },
        )


async def post_publish_results_to_slack(
    post_id: UUID,
    results: list[tuple[str, str, str | None]],
) -> None:
    """Reply in the Slack thread with publish results and permalinks.

    Args:
        post_id: Social post UUID
        results: List of (platform, status, permalink_or_error)
    """
    import httpx

    async with get_read_session() as session:
        post = await session.get(SocialPost, post_id)
        if not post or not post.slack_channel_id or not post.slack_message_ts:
            return

        channel = post.slack_channel_id
        thread_ts = post.slack_message_ts

    if not settings.slack_bot_token:
        return

    lines = []
    for platform, status, detail in results:
        if status == "published":
            if detail:
                lines.append(f"*{platform}*: {detail}")
            else:
                lines.append(f"*{platform}*: published")
        elif status == "skipped":
            lines.append(f"*{platform}*: skipped — {detail or 'not configured'}")
        else:
            lines.append(f"*{platform}*: failed — {detail or 'unknown error'}")

    text = "\n".join(lines)

    # Post as thread reply
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
            json={
                "channel": channel,
                "thread_ts": thread_ts,
                "text": text,
                "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": text}}],
            },
        )

    # Also update the original message
    had_failure = any(s == "failed" for _, s, _ in results)
    had_skip = any(s == "skipped" for _, s, _ in results)
    if had_failure:
        summary = "Publishing completed with errors"
    elif had_skip:
        summary = "Published (some platforms skipped)"
    else:
        summary = "Published to all platforms"
    await update_post_status_in_slack(post_id, summary)
