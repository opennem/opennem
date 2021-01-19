# pylint: disable=no-member
"""
Update indexes on mvs

Revision ID: 405b2ea7b351
Revises: 12c8cbba29f0
Create Date: 2021-01-19 17:17:22.558587

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "405b2ea7b351"
down_revision = "12c8cbba29f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("drop index if exists idx_mv_facility_all_trading_interval_day_aest;")

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_facility_unique ON mv_facility_all (trading_interval, network_id, code);"
    )


def downgrade() -> None:
    pass
