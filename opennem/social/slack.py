"""Slack integration for the social media pipeline.

The approval message is a single Block Kit post with the image embedded —
keeps the image visible after publish (no chat.update wiping it). Status
transitions are signalled via emoji reactions on that message, plus a
thread reply with platform permalinks once publishing finishes.

All Slack notification calls are non-fatal: a Slack API hiccup must never
fail the underlying social publish. Errors are logged + sent as Sentry
breadcrumbs but never raised.
"""

import logging
from uuid import UUID

from opennem import settings
from opennem.clients.slack_app import (
    add_reaction,
    build_weekly_summary_approval_blocks,
    post_message_with_blocks,
    post_thread_reply,
    remove_reaction,
)
from opennem.db import get_read_session
from opennem.db.models.opennem import SocialPost

logger = logging.getLogger("opennem.social.slack")

# Reaction emoji used to signal post lifecycle
EMOJI_PUBLISHING = "hourglass_flowing_sand"
EMOJI_PUBLISHED = "white_check_mark"
EMOJI_PARTIAL = "warning"
EMOJI_FAILED = "x"
EMOJI_REJECTED = "no_entry_sign"


async def send_approval_request(
    post_id: UUID,
    text_content: str,
    image_url: str | None = None,
) -> tuple[str | None, str | None]:
    """Post a single Block Kit approval message containing the image preview
    plus Approve/Reject buttons.

    Returns (channel_id, message_ts) for downstream reactions/threading.
    """
    channel = settings.slack_weekly_summary_channel
    if not channel:
        logger.warning("slack_weekly_summary_channel not configured")
        return None, None

    callback_value = str(post_id)
    truncated = text_content[:200] + "..." if len(text_content) > 200 else text_content
    blocks = build_weekly_summary_approval_blocks(
        summary_text=truncated,
        image_url=image_url,
        image_alt="Social media post preview",
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


async def mark_publishing(post_id: UUID, approved_by: str) -> None:
    """Switch the approval message from pending → publishing: add hourglass
    reaction and post a thread note announcing who approved it."""
    async with get_read_session() as session:
        post = await session.get(SocialPost, post_id)
        if not post or not post.slack_channel_id or not post.slack_message_ts:
            return
        channel = post.slack_channel_id
        ts = post.slack_message_ts

    await add_reaction(channel, ts, EMOJI_PUBLISHING)
    await post_thread_reply(channel, ts, f":hourglass_flowing_sand: Approved by @{approved_by} — publishing…")


async def mark_rejected(post_id: UUID, rejected_by: str) -> None:
    """Mark the approval message as rejected via reaction + thread note."""
    async with get_read_session() as session:
        post = await session.get(SocialPost, post_id)
        if not post or not post.slack_channel_id or not post.slack_message_ts:
            return
        channel = post.slack_channel_id
        ts = post.slack_message_ts

    await add_reaction(channel, ts, EMOJI_REJECTED)
    await post_thread_reply(channel, ts, f":no_entry_sign: Rejected by @{rejected_by}.")


async def post_publish_results_to_slack(
    post_id: UUID,
    results: list[tuple[str, str, str | None]],
) -> None:
    """Post platform permalinks as a thread reply and tag the original message
    with success/partial/failure reactions.

    Args:
        post_id: Social post UUID
        results: List of (platform, status, permalink_or_error)
    """
    async with get_read_session() as session:
        post = await session.get(SocialPost, post_id)
        if not post or not post.slack_channel_id or not post.slack_message_ts:
            return
        channel = post.slack_channel_id
        ts = post.slack_message_ts

    lines: list[str] = []
    for platform, status, detail in results:
        if status == "published":
            lines.append(f"*{platform}*: {detail}" if detail else f"*{platform}*: published")
        elif status == "skipped":
            lines.append(f"*{platform}*: skipped — {detail or 'not configured'}")
        else:
            lines.append(f"*{platform}*: failed — {detail or 'unknown error'}")

    await post_thread_reply(channel, ts, "\n".join(lines))

    had_failure = any(s == "failed" for _, s, _ in results)
    had_skip = any(s == "skipped" for _, s, _ in results)
    had_published = any(s == "published" for _, s, _ in results)

    # Drop the in-flight hourglass and add the terminal status reaction
    await remove_reaction(channel, ts, EMOJI_PUBLISHING)
    if had_failure and not had_published:
        await add_reaction(channel, ts, EMOJI_FAILED)
    elif had_failure or had_skip:
        await add_reaction(channel, ts, EMOJI_PARTIAL)
    else:
        await add_reaction(channel, ts, EMOJI_PUBLISHED)
