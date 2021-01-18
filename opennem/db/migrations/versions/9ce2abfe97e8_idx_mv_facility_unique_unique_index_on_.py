# pylint: disable=no-member
"""
idx_mv_facility_unique unique index on mv_facility_all

Revision ID: 9ce2abfe97e8
Revises: e161acce7727
Create Date: 2021-01-18 18:39:19.623430

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "9ce2abfe97e8"
down_revision = "e161acce7727"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_facility_unique ON mv_facility_all (trading_interval, network_id, code);"
    )


def downgrade() -> None:
    op.execute("drop index idx_mv_facility_unique;")
