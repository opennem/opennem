# pylint: disable=no-member
"""
merge heads 0917d7d2ae72 and 30d00d79c68a

Revision ID: 61b31447e61b
Revises: 0917d7d2ae72, 30d00d79c68a
Create Date: 2024-08-03 12:36:16.540113

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "61b31447e61b"
down_revision = ("0917d7d2ae72", "30d00d79c68a")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_stats_country_type", "stats", ["stat_type", "country"], unique=False)
    op.create_index("ix_stats_date", "stats", [sa.text("stat_date DESC")], unique=False)


def downgrade() -> None:
    pass
