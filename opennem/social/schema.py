"""Social media pipeline schemas and enums."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from opennem.schema.core import BaseConfig


class SocialPostStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"


class PlatformStatus(StrEnum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    SKIPPED = "skipped"


class SocialPostType(StrEnum):
    WEEKLY_SUMMARY = "weekly_summary"
    MILESTONE = "milestone"
    MANUAL = "manual"


class Platform(StrEnum):
    TWITTER = "twitter"
    BLUESKY = "bluesky"
    LINKEDIN = "linkedin"


ALL_PLATFORMS = [Platform.TWITTER, Platform.BLUESKY, Platform.LINKEDIN]


class CreateSocialPostRequest(BaseConfig):
    post_type: SocialPostType
    text_content: str
    image_url: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    network_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    platforms: list[Platform] = Field(default_factory=lambda: list(ALL_PLATFORMS))
    auto_approve: bool = False


class PlatformStatusResponse(BaseConfig):
    platform: str
    status: str
    permalink: str | None = None
    error_message: str | None = None
    published_at: datetime | None = None


class SocialPostResponse(BaseConfig):
    id: UUID
    post_type: str
    text_content: str
    image_url: str | None = None
    status: str
    source_type: str | None = None
    source_id: str | None = None
    network_id: str | None = None
    metadata: dict = {}
    platforms: list[PlatformStatusResponse] = []
    approved_by: str | None = None
    created_at: datetime
    approved_at: datetime | None = None
    published_at: datetime | None = None
