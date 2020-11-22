# pylint: disable=no-member
"""
update indicies that aren't used

Revision ID: 4bf86ff5c8ff
Revises: 64987ea01b57
Create Date: 2020-11-23 02:54:29.564574

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "4bf86ff5c8ff"
down_revision = "64987ea01b57"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("idx_facility_scada_trading_interval_perth_year")
    op.drop_index("idx_facility_scada_trading_interval_perth_month")
    op.drop_index("idx_facility_scada_trading_interval_perth_day")
    op.drop_index("idx_facility_scada_trading_interval_perth_hour")

    op.drop_index("idx_balancing_summary_trading_interval_perth_year")
    op.drop_index("idx_balancing_summary_trading_interval_perth_month")
    op.drop_index("idx_balancing_summary_trading_interval_perth_day")
    op.drop_index("idx_balancing_summary_trading_interval_perth_hour")

    op.drop_index("idx_facility_scada_trading_interval_sydney_year")
    op.drop_index("idx_facility_scada_trading_interval_sydney_month")
    op.drop_index("idx_facility_scada_trading_interval_sydney_day")
    op.drop_index("idx_facility_scada_trading_interval_sydney_hour")

    op.drop_index("idx_balancing_summary_trading_interval_sydney_year")
    op.drop_index("idx_balancing_summary_trading_interval_sydney_month")
    op.drop_index("idx_balancing_summary_trading_interval_sydney_day")
    op.drop_index("idx_balancing_summary_trading_interval_sydney_hour")


def downgrade():
    pass
