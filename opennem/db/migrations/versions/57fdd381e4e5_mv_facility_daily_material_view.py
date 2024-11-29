# pylint: disable=no-member
"""
mv_facility_daily material view

Revision ID: 57fdd381e4e5
Revises: a328885a3ff7
Create Date: 2024-12-02 10:25:29.744334

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57fdd381e4e5'
down_revision = 'a328885a3ff7'
branch_labels = None
depends_on = None

# Use raw SQL to handle TimescaleDB-specific operations
def upgrade():
    # Disable transaction for TimescaleDB operations
    connection = op.get_bind()

    try:
        # Create continuous aggregate materialized view
        connection.execute(sa.text("""
        CREATE MATERIALIZED VIEW mv_facility_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', interval) AS interval,
            network_id,
            network_region,
            fueltech_code,
            facility_code,
            round(sum(generated)::numeric, 4) AS generated,
            round(sum(energy)::numeric, 4) AS energy,
            round(sum(emissions)::numeric, 4) AS emissions,
            round(sum(market_value)::numeric, 4) AS market_value
        FROM at_facility_intervals
        GROUP BY 1,2,3,4,5
        """))

        # Create index on the continuous aggregate
        connection.execute(sa.text("""
        CREATE INDEX idx_mv_facility_daily
        ON mv_facility_daily (interval, network_id, network_region, fueltech_code, facility_code)
        """))

        # Add refresh policy for the continuous aggregate
        connection.execute(sa.text("""
        SELECT add_continuous_aggregate_policy('mv_facility_daily',
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
        # Drop refresh policy (if applicable)
        connection.execute(sa.text("""
        SELECT remove_continuous_aggregate_policy('mv_facility_daily')
        """))

        # Drop the materialized view
        connection.execute(sa.text("""
        DROP MATERIALIZED VIEW IF EXISTS mv_facility_daily
        """))

    except Exception as e:
        print(f"Error in downgrade: {e}")
        raise
