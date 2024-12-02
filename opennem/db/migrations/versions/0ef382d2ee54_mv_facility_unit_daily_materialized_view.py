# pylint: disable=no-member
"""
mv_facility_unit_daily materialized view

Revision ID: 0ef382d2ee54
Revises: 88bf3b34b1f7
Create Date: 2024-12-02 10:55:07.751007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ef382d2ee54'
down_revision = '88bf3b34b1f7'
branch_labels = None
depends_on = None


def upgrade():
    # Disable transaction for TimescaleDB operations
    connection = op.get_bind()

    try:
        # Create continuous aggregate materialized view
        connection.execute(sa.text("""
        CREATE MATERIALIZED VIEW mv_facility_unit_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', interval) AS interval,
            network_id,
            network_region,
            facility_code,
            unit_code,
            round(sum(generated)::numeric, 4) AS generated,
            round(sum(energy)::numeric, 4) AS energy,
            round(sum(emissions)::numeric, 4) AS emissions,
            round(sum(market_value)::numeric, 4) AS market_value
        FROM at_facility_intervals
        GROUP BY 1,2,3,4,5
        WITH NO DATA
        """))

        # Create indexes on the materialized view
        connection.execute(sa.text("""
        CREATE INDEX idx_mv_facility_unit_daily_interval
        ON mv_facility_unit_daily (interval DESC, network_id, network_region, facility_code, unit_code)
        """))

        connection.execute(sa.text("""
        CREATE INDEX idx_mv_facility_unit_daily_facility_interval
        ON mv_facility_unit_daily (facility_code, interval DESC);
        """))

        connection.execute(sa.text("""
        CREATE INDEX idx_mv_facility_unit_daily_interval_only
        ON mv_facility_unit_daily (interval DESC);
        """))

        connection.execute(sa.text("""
        CREATE INDEX idx_mv_facility_unit_daily_network
        ON mv_facility_unit_daily (network_id, network_region, facility_code, unit_code, interval DESC)
        """))

        # Add refresh policy
        connection.execute(sa.text("""
        SELECT add_continuous_aggregate_policy('mv_facility_unit_daily',
            start_offset => INTERVAL '3 days',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour')
        """))

    except Exception as e:
        print(f"Error in upgrade: {e}")
        raise

def downgrade():
    # Disable transaction for TimescaleDB operations
    connection = op.get_bind()

    try:
        # Drop refresh policy
        connection.execute(sa.text("""
        SELECT remove_continuous_aggregate_policy('mv_facility_unit_daily')
        """))

        # Drop the materialized view
        connection.execute(sa.text("""
        DROP MATERIALIZED VIEW IF EXISTS mv_facility_unit_daily
        """))

    except Exception as e:
        print(f"Error in downgrade: {e}")
        raise
