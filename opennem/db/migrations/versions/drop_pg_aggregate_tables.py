"""Drop PG aggregate tables — replaced by ClickHouse

All data now served from ClickHouse unit_intervals, market_summary,
and their materialized views. These PostgreSQL aggregates are no
longer populated or queried.

Revision ID: a2b3c4d5e6f7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-21
"""

from alembic import op

# revision identifiers
revision = "a2b3c4d5e6f7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop TimescaleDB continuous aggregates first (must use CASCADE)
    # These have refresh policies that need to be removed first
    op.execute("SELECT remove_continuous_aggregate_policy('mv_fueltech_daily', if_exists => true)")
    op.execute("SELECT remove_continuous_aggregate_policy('mv_facility_unit_daily', if_exists => true)")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_fueltech_daily CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_facility_unit_daily CASCADE")

    # Drop regular aggregate tables
    op.drop_table("at_facility_intervals")
    op.drop_table("at_network_demand")


def downgrade() -> None:
    # Not reversible — data was in ClickHouse, tables were empty
    raise NotImplementedError("Cannot restore dropped aggregate tables — data lives in ClickHouse")
