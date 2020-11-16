# pylint: disable=no-member
"""Updated indexes on balancing summary and facility scada

Revision ID: 9ee998713b18
Revises: 3595c70244db
Create Date: 2020-10-09 02:46:14.571696

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9ee998713b18"
down_revision = "3595c70244db"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_year"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_month"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_day"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_hour"
    )

    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_year"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_month"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_day"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_hour"
    )

    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_year"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_month"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_day"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_hour"
    )


def downgrade():
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_year"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_month"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_day"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_perth_hour"
    )

    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_year"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_month"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_day"
    )
    op.execute(
        "drop index if exists idx_facility_scada_trading_interval_sydney_hour"
    )

    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_year"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_month"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_day"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_trading_interval_perth_hour"
    )

    op.execute("COMMIT")

    op.create_index(
        "idx_facility_scada_trading_interval_perth_year",
        "facility_scada",
        [
            sa.text(
                "date_trunc('year', trading_interval AT TIME ZONE 'Australia/Perth')"
            )
        ],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_perth_month",
        "facility_scada",
        [
            sa.text(
                "date_trunc('month', trading_interval AT TIME ZONE 'Australia/Perth')"
            )
        ],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_perth_day",
        "facility_scada",
        [
            sa.text(
                "date_trunc('day', trading_interval AT TIME ZONE 'Australia/Perth')"
            )
        ],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_perth_hour",
        "facility_scada",
        [
            sa.text(
                "date_trunc('hour', trading_interval AT TIME ZONE 'Australia/Perth')"
            )
        ],
        postgresql_concurrently=True,
    )

    # NEM timezone indexes
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_year",
        "facility_scada",
        [
            sa.text(
                "date_trunc('year', trading_interval AT TIME ZONE 'Australia/Sydney')"
            )
        ],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_month",
        "facility_scada",
        [
            sa.text(
                "date_trunc('month', trading_interval AT TIME ZONE 'Australia/Sydney')"
            )
        ],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_day",
        "facility_scada",
        [
            sa.text(
                "date_trunc('day', trading_interval AT TIME ZONE 'Australia/Sydney')"
            )
        ],
        postgresql_concurrently=True,
    )
    op.create_index(
        "idx_facility_scada_trading_interval_sydney_hour",
        "facility_scada",
        [
            sa.text(
                "date_trunc('hour', trading_interval AT TIME ZONE 'Australia/Sydney')"
            )
        ],
        postgresql_concurrently=True,
    )
