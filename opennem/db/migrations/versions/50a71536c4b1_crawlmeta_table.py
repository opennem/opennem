# pylint: disable=no-member
"""
crawlmeta table

Revision ID: 50a71536c4b1
Revises: 77bf497fb398
Create Date: 2021-05-28 20:52:10.996062

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "50a71536c4b1"
down_revision = "77bf497fb398"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crawl_meta",
        sa.Column("spider_name", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("spider_name"),
    )
    op.create_index(op.f("ix_crawl_meta_value"), "crawl_meta", ["value"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_crawl_meta_value"), table_name="crawl_meta")
    op.drop_table("crawl_meta")
