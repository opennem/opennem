# pylint: disable=no-member
"""
rename crawlmeta value to data

Revision ID: 5bf4716b7da9
Revises: 50a71536c4b1
Create Date: 2021-05-28 22:37:30.253796

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5bf4716b7da9"
down_revision = "50a71536c4b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("crawl_meta", "value", new_column_name="data")
    op.drop_index("ix_crawl_meta_value", table_name="crawl_meta")
    op.create_index(op.f("ix_crawl_meta_data"), "crawl_meta", ["data"], unique=False)


def downgrade() -> None:
    op.alter_column("crawl_meta", "data", new_column_name="value")
    op.drop_index(op.f("ix_crawl_meta_data"), table_name="crawl_meta")
    op.create_index("ix_crawl_meta_value", "crawl_meta", ["value"], unique=False)
