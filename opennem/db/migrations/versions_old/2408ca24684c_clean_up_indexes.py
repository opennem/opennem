# pylint: disable=no-member
"""
clean up indexes

Revision ID: 2408ca24684c
Revises: 9765ef882492
Create Date: 2023-03-14 08:28:16.322922

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2408ca24684c"
down_revision = "9765ef882492"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("drop index if exists idx_facility_scada_trading_interval_desc_facility_code;")
    op.execute("drop index if exists idx_facility_scada_day_network_fueltech_aest;")
    op.execute("drop index if exists idx_facility_scada_day_network_fueltech_awst;")
    op.execute("drop index if exists idx_facility_scada_trading_interval_perth_day;")
    op.execute("drop index if exists idx_facility_scada_trading_interval_perth_month;")
    op.execute("drop index if exists idx_facility_scada_trading_interval_sydney_day;")
    op.execute("drop index if exists idx_facility_scada_trading_interval_sydney_month;")
    op.execute("drop index if exists idx_facility_scada_trading_interval_facility_code;")


def downgrade() -> None:
    pass
