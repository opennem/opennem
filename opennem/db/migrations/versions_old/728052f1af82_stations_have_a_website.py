# pylint: disable=no-member
"""
Stations have a website

Revision ID: 728052f1af82
Revises: 51638d9a9c90
Create Date: 2021-03-12 21:01:34.701392

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "728052f1af82"
down_revision = "51638d9a9c90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("station", sa.Column("website_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("station", "website_url")
