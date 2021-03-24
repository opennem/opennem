# pylint: disable=no-member
"""
Create indexes on mv_facility_all for interval orders

Revision ID: c96f1bd608d9
Revises: afdb5be8ac11
Create Date: 2021-03-24 14:28:33.337266

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c96f1bd608d9"
down_revision = "afdb5be8ac11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "create index if not exists idx_trading_interval_code_index on mv_facility_all (trading_interval desc, code)"
    )

    op.execute(
        "create index if not exists idx_trading_day_aest_code_index on mv_facility_all (ti_day_aest desc, code);"
    )

    op.execute(
        "create index if not exists idx_trading_month_aest_code_index on mv_facility_all (ti_month_aest desc, code);"
    )

    op.execute(
        "create index if not exists idx_trading_day_awst_code_index on mv_facility_all (ti_day_awst desc, code);"
    )

    op.execute(
        "create index if not exists idx_trading_month_awst_code_index on mv_facility_all (ti_month_awst desc, code);"
    )


def downgrade() -> None:
    pass
