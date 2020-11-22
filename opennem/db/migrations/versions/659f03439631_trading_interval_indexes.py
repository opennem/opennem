# pylint: disable=no-member
"""Trading interval indexes

Revision ID: 659f03439631
Revises: 9ee998713b18
Create Date: 2020-10-09 03:01:56.054462

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "659f03439631"
down_revision = "9ee998713b18"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("COMMIT")

    op.create_index(
        "idx_facility_scada_trading_interval_perth_year",
        "facility_scada",
        [sa.text("date_trunc('year', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_perth_month",
        "facility_scada",
        [sa.text("date_trunc('month', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_perth_day",
        "facility_scada",
        [sa.text("date_trunc('day', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_perth_hour",
        "facility_scada",
        [sa.text("date_trunc('hour', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )

    # wem balancing summary
    op.create_index(
        "idx_balancing_summary_trading_interval_perth_year",
        "balancing_summary",
        [sa.text("date_trunc('year', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_balancing_summary_trading_interval_perth_month",
        "balancing_summary",
        [sa.text("date_trunc('month', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_balancing_summary_trading_interval_perth_day",
        "balancing_summary",
        [sa.text("date_trunc('day', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_balancing_summary_trading_interval_perth_hour",
        "balancing_summary",
        [sa.text("date_trunc('hour', trading_interval AT TIME ZONE 'AWST')")],
        postgresql_concurrently=True,
    )

    # NEM timezone indexes
    # facility scada
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_year",
        "facility_scada",
        [sa.text("date_trunc('year', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_month",
        "facility_scada",
        [sa.text("date_trunc('month', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_day",
        "facility_scada",
        [sa.text("date_trunc('day', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_hour",
        "facility_scada",
        [sa.text("date_trunc('hour', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )

    # NEM balancing summary
    op.create_index(
        "idx_balancing_summary_trading_interval_sydney_year",
        "balancing_summary",
        [sa.text("date_trunc('year', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_balancing_summary_trading_interval_sydney_month",
        "balancing_summary",
        [sa.text("date_trunc('month', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_balancing_summary_trading_interval_sydney_day",
        "balancing_summary",
        [sa.text("date_trunc('day', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_balancing_summary_trading_interval_sydney_hour",
        "balancing_summary",
        [sa.text("date_trunc('hour', trading_interval AT TIME ZONE 'AEST')")],
        postgresql_concurrently=True,
    )


def downgrade():
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
