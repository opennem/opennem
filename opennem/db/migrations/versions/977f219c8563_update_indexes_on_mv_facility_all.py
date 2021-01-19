# pylint: disable=no-member
"""
Update indexes on mv_facility_all

Revision ID: 977f219c8563
Revises: f21b1048faf6
Create Date: 2021-01-19 15:24:52.893563

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "977f219c8563"
down_revision = "f21b1048faf6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("drop index if exists idx_mv_facility_all_trading_interval_day_aest;")

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_facility_unique ON mv_facility_all (trading_interval, network_id, code);"
    )


def downgrade() -> None:
    pass
