"""Social media posting pipeline.

Core functions for creating, approving, rejecting, and publishing social posts.
All content sources (weekly summary, recordreactor, manual) flow through here.
"""

import io
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem import settings
from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import SocialPost, SocialPostPlatform
from opennem.social.schema import (
    CreateSocialPostRequest,
    Platform,
    PlatformStatus,
    PlatformStatusResponse,
    SocialPostResponse,
    SocialPostStatus,
)
from opennem.social.slack import post_publish_results_to_slack, send_approval_request, update_post_status_in_slack

logger = logging.getLogger("opennem.social.pipeline")


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def create_social_post(
    req: CreateSocialPostRequest,
    image: bytes | None = None,
) -> SocialPostResponse:
    """Create a social post, send to Slack for approval."""
    # Upload image to Cloudflare if provided. The CF-hosted URL is required
    # for downstream Twitter/Bluesky/LinkedIn publishing, so raise and halt
    # the pipeline on failure — ARQ will retry and Sentry will capture.
    image_url = req.image_url
    if image and not image_url:
        from opennem.clients.cfimage import save_image_to_cloudflare

        cfimage = await save_image_to_cloudflare(io.BytesIO(image))
        image_url = cfimage.url

    # Check for duplicate by source_id. Only rows that actually reached Slack
    # (slack_message_ts IS NOT NULL) count — orphaned rows from crashed prior
    # attempts would otherwise block re-submission forever.
    if req.source_id:
        async with get_read_session() as session:
            result = await session.execute(
                select(SocialPost.id).where(
                    SocialPost.source_type == req.source_type,
                    SocialPost.source_id == req.source_id,
                    SocialPost.slack_message_ts.is_not(None),
                )
            )
            existing_id = result.scalar_one_or_none()
            if existing_id:
                logger.info(f"Duplicate social post for {req.source_type}:{req.source_id}, skipping")
                return await get_social_post(existing_id)

    async with get_write_session() as session:
        post = SocialPost(
            post_type=req.post_type,
            text_content=req.text_content,
            image_url=image_url,
            status=SocialPostStatus.PENDING_APPROVAL,
            source_type=req.source_type,
            source_id=req.source_id,
            network_id=req.network_id,
            metadata_=req.metadata or {},
        )
        session.add(post)
        await session.flush()

        for platform in req.platforms:
            plat = SocialPostPlatform(
                post_id=post.id,
                platform=platform,
                status=PlatformStatus.PENDING,
            )
            session.add(plat)

        await session.flush()
        post_id = post.id
        await session.commit()

    # Post to Slack for approval
    channel = settings.slack_weekly_summary_channel
    if channel and not req.auto_approve:
        slack_channel_id, slack_message_ts = await send_approval_request(post_id, req.text_content, image)

        if slack_channel_id and slack_message_ts:
            async with get_write_session() as session:
                post = await session.get(SocialPost, post_id)
                if post:
                    post.slack_channel_id = slack_channel_id
                    post.slack_message_ts = slack_message_ts
                await session.commit()

    if req.auto_approve:
        await approve_social_post(post_id, approved_by="auto")

    return await get_social_post(post_id)


async def approve_social_post(post_id: UUID, approved_by: str) -> None:
    """Mark post as approved and enqueue publishing."""
    async with get_write_session() as session:
        post = await session.get(SocialPost, post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return

        if post.status not in (SocialPostStatus.PENDING_APPROVAL, SocialPostStatus.DRAFT):
            logger.warning(f"Post {post_id} status is {post.status}, cannot approve")
            return

        post.status = SocialPostStatus.APPROVED
        post.approved_by = approved_by
        post.approved_at = _utcnow()
        await session.commit()

    await update_post_status_in_slack(post_id, f"Approved by @{approved_by} — publishing...")
    await publish_social_post(post_id)


async def reject_social_post(post_id: UUID, rejected_by: str) -> None:
    """Mark post as rejected."""
    async with get_write_session() as session:
        post = await session.get(SocialPost, post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return

        post.status = SocialPostStatus.REJECTED
        post.rejected_by = rejected_by
        await session.commit()

    await update_post_status_in_slack(post_id, f"Rejected by @{rejected_by}")


async def publish_social_post(post_id: UUID) -> None:
    """Publish to all pending platforms, update statuses, notify Slack."""
    from opennem.clients.bluesky import post_bluesky, post_bluesky_with_image
    from opennem.clients.linkedin import post_linkedin
    from opennem.clients.twitter import post_tweet, post_tweet_with_image

    # Load post + platforms
    async with get_read_session() as session:
        result = await session.execute(
            select(SocialPost).where(SocialPost.id == post_id).options(selectinload(SocialPost.platforms))
        )
        post = result.scalar_one_or_none()
        if not post:
            logger.error(f"Post {post_id} not found for publishing")
            return

        text = post.text_content
        image_url = post.image_url
        platforms = list(post.platforms)

    # Set status to publishing
    async with get_write_session() as session:
        post = await session.get(SocialPost, post_id)
        if post:
            post.status = SocialPostStatus.PUBLISHING
        await session.commit()

    # Download image if we have a URL
    image_bytes: bytes | None = None
    if image_url:
        try:
            from opennem.utils.http import http_factory

            client = http_factory(proxy=False, mimic_browser=False)
            resp = await client.get(image_url)
            if resp.status_code == 200:
                image_bytes = resp.content
        except Exception as e:
            logger.warning(f"Failed to download image from {image_url}: {e}")

    # Platform-specific publish functions
    async def _publish_twitter(txt: str, img: bytes | None) -> None:
        if img:
            await post_tweet_with_image(txt, io.BytesIO(img))
        else:
            await post_tweet(txt)

    async def _publish_bluesky(txt: str, img: bytes | None) -> None:
        if img:
            await post_bluesky_with_image(txt, io.BytesIO(img), alt_text="Open Electricity")
        else:
            await post_bluesky(txt)

    async def _publish_linkedin(txt: str, img: bytes | None) -> None:
        await post_linkedin(txt, io.BytesIO(img) if img else None)

    platform_publishers: dict[str, Any] = {
        Platform.TWITTER: _publish_twitter,
        Platform.BLUESKY: _publish_bluesky,
        Platform.LINKEDIN: _publish_linkedin,
    }

    published_count = 0
    failed_count = 0
    all_results: list[tuple[str, str, str | None]] = []

    for plat in platforms:
        if plat.status != PlatformStatus.PENDING:
            continue

        publisher = platform_publishers.get(plat.platform)
        if not publisher:
            logger.warning(f"No publisher for platform {plat.platform}")
            continue

        # Set platform status to publishing
        async with get_write_session() as session:
            p = await session.get(SocialPostPlatform, plat.id)
            if p:
                p.status = PlatformStatus.PUBLISHING
            await session.commit()

        try:
            await publisher(text, image_bytes)
            async with get_write_session() as session:
                p = await session.get(SocialPostPlatform, plat.id)
                if p:
                    p.status = PlatformStatus.PUBLISHED
                    p.published_at = _utcnow()
                await session.commit()
            all_results.append((plat.platform, "published", None))
            published_count += 1
            logger.info(f"Published to {plat.platform}")
        except Exception as e:
            logger.error(f"Failed to publish to {plat.platform}: {e}")
            async with get_write_session() as session:
                p = await session.get(SocialPostPlatform, plat.id)
                if p:
                    p.status = PlatformStatus.FAILED
                    p.error_message = str(e)[:500]
                await session.commit()
            all_results.append((plat.platform, "failed", str(e)))
            failed_count += 1

    # Update overall post status
    async with get_write_session() as session:
        post = await session.get(SocialPost, post_id)
        if post:
            if failed_count > 0 and published_count > 0:
                post.status = SocialPostStatus.PUBLISHED  # partial success still counts
                post.published_at = _utcnow()
            elif failed_count > 0:
                post.status = SocialPostStatus.FAILED
            else:
                post.status = SocialPostStatus.PUBLISHED
                post.published_at = _utcnow()
        await session.commit()

    await post_publish_results_to_slack(post_id, all_results)


async def retry_social_post(post_id: UUID) -> None:
    """Retry failed platforms for a post."""
    async with get_write_session() as session:
        result = await session.execute(
            select(SocialPostPlatform).where(
                SocialPostPlatform.post_id == post_id,
                SocialPostPlatform.status == PlatformStatus.FAILED,
            )
        )
        failed = result.scalars().all()
        for plat in failed:
            plat.status = PlatformStatus.PENDING
            plat.error_message = None

        post = await session.get(SocialPost, post_id)
        if post:
            post.status = SocialPostStatus.APPROVED
        await session.commit()

    await publish_social_post(post_id)


async def get_social_post(post_id: UUID) -> SocialPostResponse | None:
    """Load a social post with platform statuses."""
    async with get_read_session() as session:
        result = await session.execute(
            select(SocialPost).where(SocialPost.id == post_id).options(selectinload(SocialPost.platforms))
        )
        post = result.scalar_one_or_none()
        if not post:
            return None

        return SocialPostResponse(
            id=post.id,
            post_type=post.post_type,
            text_content=post.text_content,
            image_url=post.image_url,
            status=post.status,
            source_type=post.source_type,
            source_id=post.source_id,
            network_id=post.network_id,
            metadata=post.metadata_ or {},
            platforms=[
                PlatformStatusResponse(
                    platform=p.platform,
                    status=p.status,
                    permalink=p.permalink,
                    error_message=p.error_message,
                    published_at=p.published_at,
                )
                for p in post.platforms
            ],
            approved_by=post.approved_by,
            created_at=post.created_at,
            approved_at=post.approved_at,
            published_at=post.published_at,
        )
