# pylint: disable=no-member
"""
crawl_history table

Revision ID: 5b5f4a4957ed
Revises: a61d4d4b3080
Create Date: 2022-06-23 03:12:51.544546

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5b5f4a4957ed"
down_revision = "a61d4d4b3080"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crawl_history",
        sa.Column(
            "source",
            sa.Enum("nemweb", "wem", name="crawlersource"),
            nullable=False,
        ),
        sa.Column("crawler_name", sa.Text(), nullable=False),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column("interval", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("inserted_records", sa.Integer(), nullable=True),
        sa.Column(
            "crawled_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "processed_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["network_id"], ["network.code"], name="fk_crawl_info_network_code"),
        sa.PrimaryKeyConstraint("source", "crawler_name", "network_id", "interval"),
    )
    op.create_index(
        op.f("ix_crawl_history_interval"),
        "crawl_history",
        ["interval"],
        unique=False,
    )
    op.execute("select create_hypertable('crawl_history', 'interval', migrate_data=>true, if_not_exists=>true)")


def downgrade() -> None:
    op.drop_index(op.f("ix_crawl_history_interval"), table_name="crawl_history")
    op.drop_table("crawl_history")
