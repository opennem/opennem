# pylint: disable=no-member
"""
Indexes for day truncs in NEM and WEM timezones

Revision ID: d7c22e0add08
Revises: df7308f58ee2
Create Date: 2020-12-02 02:00:14.521669

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d7c22e0add08"
down_revision = "df7308f58ee2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_facility_scada_trading_interval_perth_day",
        "facility_scada",
        [sa.text("date_trunc('day', trading_interval AT TIME ZONE 'AWST')")],
    )

    op.create_index(
        "idx_facility_scada_trading_interval_sydney_day",
        "facility_scada",
        [sa.text("date_trunc('day', trading_interval AT TIME ZONE 'AEST')")],
    )


def downgrade() -> None:
    op.drop_index("idx_facility_scada_trading_interval_perth_day")
    op.drop_index("idx_facility_scada_trading_interval_sydney_day")
