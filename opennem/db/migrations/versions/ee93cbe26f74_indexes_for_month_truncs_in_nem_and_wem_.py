# pylint: disable=no-member
"""
Indexes for month truncs in NEM and WEM timezones

Revision ID: ee93cbe26f74
Revises: d7c22e0add08
Create Date: 2020-12-02 02:04:33.054920

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ee93cbe26f74"
down_revision = "d7c22e0add08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_facility_scada_trading_interval_perth_month",
        "facility_scada",
        [sa.text("date_trunc('month', trading_interval AT TIME ZONE 'AWST')")],
    )

    op.create_index(
        "idx_facility_scada_trading_interval_sydney_month",
        "facility_scada",
        [sa.text("date_trunc('month', trading_interval AT TIME ZONE 'AEST')")],
    )


def downgrade() -> None:
    op.drop_index("idx_facility_scada_trading_interval_perth_month")
    op.drop_index("idx_facility_scada_trading_interval_sydney_month")
