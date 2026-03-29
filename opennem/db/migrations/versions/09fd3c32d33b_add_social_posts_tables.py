"""add social_posts and social_post_platforms tables

Revision ID: 09fd3c32d33b
Revises: c4d5e6f7a8b9
Create Date: 2026-03-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

revision = "09fd3c32d33b"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_posts",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("post_type", sa.String(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("slack_channel_id", sa.String(), nullable=True),
        sa.Column("slack_message_ts", sa.String(), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("rejected_by", sa.String(), nullable=True),
        sa.Column("network_id", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("approved_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("published_at", TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_social_posts_status", "social_posts", ["status"])
    op.create_index("idx_social_posts_created_at", "social_posts", ["created_at"])
    op.create_index("idx_social_posts_source", "social_posts", ["source_type", "source_id"])

    op.create_table(
        "social_post_platforms",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("post_id", UUID(as_uuid=True), sa.ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("permalink", sa.Text(), nullable=True),
        sa.Column("platform_post_id", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("published_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "platform", name="uq_social_post_platform"),
    )


def downgrade() -> None:
    op.drop_table("social_post_platforms")
    op.drop_table("social_posts")
