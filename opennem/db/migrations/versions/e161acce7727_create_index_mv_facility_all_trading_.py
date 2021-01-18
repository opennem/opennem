# pylint: disable=no-member
"""
Create index mv_facility_all_trading_interval

Revision ID: e161acce7727
Revises: 98e2968b63e4
Create Date: 2021-01-18 18:29:47.808544

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e161acce7727"
down_revision = "98e2968b63e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "create index if not exists idx_mv_facility_all_trading_interval_day_aest on mv_facility_all (date_trunc('day'::text, timezone('AEST'::text, trading_interval)) DESC, fueltech_id);"
    )


def downgrade() -> None:
    op.execute("drop index idx_mv_facility_all_trading_interval_day_aest;")
