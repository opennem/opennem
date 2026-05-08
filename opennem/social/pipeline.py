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
from opennem.social.slack import (
    mark_publishing,
    mark_rejected,
    post_publish_results_to_slack,
    send_approval_request,
)

logger = logging.getLogger("opennem.social.pipeline")


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def create_social_post(
    req: CreateSocialPostRequest,
    image: bytes | None = None,
) -> "SocialPostResponse | None":
    """Create a social post, send to Slack for approval."""
    # Upload image to Cloudflare if provided. Store the `hires` variant URL —
    # the default `public` variant scales down to 1366px and re-encodes as
    # JPEG, which tanks quality on Twitter. `hires` preserves the full PNG.
    image_url = req.image_url
    if image and not image_url:
        from opennem.clients.cfimage import save_image_to_cloudflare

        cfimage = await save_image_to_cloudflare(io.BytesIO(image))
        image_url = cfimage.hires_url

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

    # Persist link_url in metadata so we can read it back at publish time
    metadata_dict: dict[str, Any] = dict(req.metadata or {})
    if req.link_url:
        metadata_dict["link_url"] = req.link_url

    async with get_write_session() as session:
        post = SocialPost(
            post_type=req.post_type,
            text_content=req.text_content,
            image_url=image_url,
            status=SocialPostStatus.PENDING_APPROVAL,
            source_type=req.source_type,
            source_id=req.source_id,
            network_id=req.network_id,
            metadata_=metadata_dict,
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

    # Post to Slack for approval — single Block Kit message with the image embedded
    channel = settings.slack_weekly_summary_channel
    if channel and not req.auto_approve:
        slack_channel_id, slack_message_ts = await send_approval_request(post_id, req.text_content, image_url=image_url)

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

    await mark_publishing(post_id, approved_by)
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

    await mark_rejected(post_id, rejected_by)


async def publish_social_post(post_id: UUID) -> None:
    """Publish to all pending platforms, persist permalinks, post URL replies on
    Twitter/Bluesky for `link_url`, then notify Slack."""
    from opennem.clients.bluesky import post_bluesky, post_bluesky_reply, post_bluesky_with_image
    from opennem.clients.linkedin import LinkedInNotConfiguredError, post_linkedin
    from opennem.clients.twitter import post_tweet, post_tweet_reply, post_tweet_with_image

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
        link_url = (post.metadata_ or {}).get("link_url") if post.metadata_ else None

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

    # Each publisher returns {platform_post_id, permalink, ...} (or {} when not
    # supported / not implemented). Failures raise.
    #
    # When `link_url` is set, the URL is contractually part of the post —
    # Twitter/Bluesky main bodies have it stripped — so a failed reply must fail
    # the platform publish. The main post is already up at that point; the FAILED
    # row carries the permalink so an operator can manually post the reply or
    # accept the linkless post. (A pipeline retry would duplicate the main post.)
    async def _publish_twitter(txt: str, img: bytes | None) -> dict:
        if img:
            result = await post_tweet_with_image(txt, io.BytesIO(img))
        else:
            result = await post_tweet(txt)
        if link_url and result and result.get("platform_post_id"):
            try:
                await post_tweet_reply(link_url, in_reply_to_tweet_id=result["platform_post_id"])
            except Exception as e:
                permalink = result.get("permalink") or "no permalink"
                raise RuntimeError(f"Twitter main post {permalink} succeeded but URL thread reply failed: {e}") from e
        return result or {}

    async def _publish_bluesky(txt: str, img: bytes | None) -> dict:
        if img:
            result = await post_bluesky_with_image(txt, io.BytesIO(img), alt_text="Open Electricity")
        else:
            result = await post_bluesky(txt)
        if link_url and result and result.get("platform_post_id") and result.get("cid"):
            try:
                await post_bluesky_reply(
                    link_url,
                    parent_uri=result["platform_post_id"],
                    parent_cid=result["cid"],
                )
            except Exception as e:
                permalink = result.get("permalink") or "no permalink"
                raise RuntimeError(f"Bluesky main post {permalink} succeeded but URL thread reply failed: {e}") from e
        return result or {}

    async def _publish_linkedin(txt: str, img: bytes | None) -> dict:
        # LinkedIn doesn't penalise URLs; append inline if present
        body = f"{txt}\n\n{link_url}" if link_url else txt
        result = await post_linkedin(body, io.BytesIO(img) if img else None)
        return result or {}

    platform_publishers: dict[str, Any] = {
        Platform.TWITTER: _publish_twitter,
        Platform.BLUESKY: _publish_bluesky,
        Platform.LINKEDIN: _publish_linkedin,
    }

    published_count = 0
    failed_count = 0
    skipped_count = 0
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
            result = await publisher(text, image_bytes)
            permalink = result.get("permalink") if isinstance(result, dict) else None
            platform_post_id = result.get("platform_post_id") if isinstance(result, dict) else None

            async with get_write_session() as session:
                p = await session.get(SocialPostPlatform, plat.id)
                if p:
                    p.status = PlatformStatus.PUBLISHED
                    p.published_at = _utcnow()
                    if permalink:
                        p.permalink = permalink
                    if platform_post_id:
                        p.platform_post_id = str(platform_post_id)
                await session.commit()
            # Slack thread reply uses the permalink if we have one, else "published"
            all_results.append((plat.platform, "published", permalink))
            published_count += 1
            logger.info(f"Published to {plat.platform}: {permalink or 'no permalink'}")
        except LinkedInNotConfiguredError as e:
            async with get_write_session() as session:
                p = await session.get(SocialPostPlatform, plat.id)
                if p:
                    p.status = PlatformStatus.SKIPPED
                    p.error_message = str(e)[:500]
                await session.commit()
            all_results.append((plat.platform, "skipped", "credentials not configured"))
            skipped_count += 1
            logger.info(f"Skipped {plat.platform}: not configured")
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
            elif published_count > 0:
                post.status = SocialPostStatus.PUBLISHED
                post.published_at = _utcnow()
            else:
                # only skips, no real publishes
                post.status = SocialPostStatus.FAILED
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
