# pylint: disable=no-member
"""
clean up indexes

Revision ID: 2408ca24684c
Revises: 9765ef882492
Create Date: 2023-03-14 08:28:16.322922

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2408ca24684c"
down_revision = "9765ef882492"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    drop index if exists idx_facility_scada_trading_interval_desc_facility_code;
    drop index if exists idx_facility_scada_day_network_fueltech_aest;
    drop index if exists idx_facility_scada_day_network_fueltech_awst;
    drop index if exists idx_facility_scada_trading_interval_perth_day;
    drop index if exists idx_facility_scada_trading_interval_perth_month;
    drop index if exists idx_facility_scada_trading_interval_sydney_day;
    drop index if exists idx_facility_scada_trading_interval_sydney_month;
    drop index if exists idx_facility_scada_trading_interval_facility_code;
    """
    )


def downgrade() -> None:
    pass
