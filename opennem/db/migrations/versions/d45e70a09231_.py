"""Add timezone indexes to facility_scada

Revision ID: d45e70a09231
Revises: 42cdf37a6e3b
Create Date: 2020-10-06 14:05:47.917286

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d45e70a09231"
down_revision = "42cdf37a6e3b"
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    op.drop_index("idx_facility_scada_trading_interval_perth_year")
    op.drop_index("idx_facility_scada_trading_interval_perth_month")
    op.drop_index("idx_facility_scada_trading_interval_perth_day")
    op.drop_index("idx_facility_scada_trading_interval_perth_hour")

    op.drop_index("idx_facility_scada_trading_interval_sydney_year")
    op.drop_index("idx_facility_scada_trading_interval_sydney_month")
    op.drop_index("idx_facility_scada_trading_interval_sydney_day")
    op.drop_index("idx_facility_scada_trading_interval_sydney_hour")

