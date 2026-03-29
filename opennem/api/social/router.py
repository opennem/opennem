"""Social media post management API."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi_versionizer.versionizer import api_version
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem.api.security import api_protected
from opennem.db import get_read_session
from opennem.db.models.opennem import SocialPost
from opennem.social.pipeline import (
    approve_social_post,
    create_social_post,
    get_social_post,
    reject_social_post,
    retry_social_post,
)
from opennem.social.schema import CreateSocialPostRequest, SocialPostResponse

logger = logging.getLogger("opennem.api.social")

router = APIRouter()


@api_version(4)
@router.get("")
@api_protected()
async def list_social_posts(
    status: str | None = None,
    post_type: str | None = None,
    limit: int = 20,
    page: int = 1,
) -> dict:
    """List social posts with optional filtering."""
    async with get_read_session() as session:
        query = select(SocialPost).options(selectinload(SocialPost.platforms))

        if status:
            query = query.where(SocialPost.status == status)
        if post_type:
            query = query.where(SocialPost.post_type == post_type)

        query = query.order_by(SocialPost.created_at.desc())
        query = query.limit(min(limit, 100)).offset((page - 1) * limit)

        result = await session.execute(query)
        posts = result.scalars().all()

    return {
        "success": True,
        "data": [
            SocialPostResponse(
                id=p.id,
                post_type=p.post_type,
                text_content=p.text_content,
                image_url=p.image_url,
                status=p.status,
                source_type=p.source_type,
                source_id=p.source_id,
                network_id=p.network_id,
                metadata=p.metadata_ or {},
                platforms=[
                    {
                        "platform": pl.platform,
                        "status": pl.status,
                        "permalink": pl.permalink,
                        "error_message": pl.error_message,
                        "published_at": pl.published_at,
                    }
                    for pl in p.platforms
                ],
                approved_by=p.approved_by,
                created_at=p.created_at,
                approved_at=p.approved_at,
                published_at=p.published_at,
            )
            for p in posts
        ],
    }


@api_version(4)
@router.get("/{post_id}")
@api_protected()
async def get_post(post_id: UUID) -> dict:
    """Get a single social post with platform statuses."""
    post = await get_social_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True, "data": post}


@api_version(4)
@router.post("")
@api_protected()
async def create_post(req: CreateSocialPostRequest) -> dict:
    """Create a new social post (manual or agent-driven)."""
    post = await create_social_post(req)
    return {"success": True, "data": post}


@api_version(4)
@router.post("/{post_id}/approve")
@api_protected()
async def approve_post(post_id: UUID, approved_by: str = "api") -> dict:
    """Approve a social post for publishing (alternative to Slack buttons)."""
    await approve_social_post(post_id, approved_by)
    post = await get_social_post(post_id)
    return {"success": True, "data": post}


@api_version(4)
@router.post("/{post_id}/reject")
@api_protected()
async def reject_post(post_id: UUID, rejected_by: str = "api") -> dict:
    """Reject a social post."""
    await reject_social_post(post_id, rejected_by)
    post = await get_social_post(post_id)
    return {"success": True, "data": post}


@api_version(4)
@router.post("/{post_id}/retry")
@api_protected()
async def retry_post(post_id: UUID) -> dict:
    """Retry publishing to failed platforms."""
    await retry_social_post(post_id)
    post = await get_social_post(post_id)
    return {"success": True, "data": post}
