# pylint: disable=no-member
"""
mv_balancing_summary material view

Revision ID: 88bf3b34b1f7
Revises: 57fdd381e4e5
Create Date: 2024-12-02 10:28:35.564537

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88bf3b34b1f7'
down_revision = '57fdd381e4e5'
branch_labels = None
depends_on = None


# Use raw SQL to handle TimescaleDB-specific operations
def upgrade():
    # Disable transaction for TimescaleDB operations
    connection = op.get_bind()

    try:
        # Create continuous aggregate materialized view with NO DATA
        connection.execute(sa.text("""
        CREATE MATERIALIZED VIEW mv_balancing_summary
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('5m', interval) as interval,
            network_id,
            network_region,
            max(demand) as demand,
            max(price) as price
        FROM balancing_summary
        WHERE
            is_forecast IS FALSE AND network_region != 'SNOWY1'
        GROUP BY 1, 2, 3
        """))

        # Add refresh policy for the continuous aggregate
        connection.execute(sa.text("""
        SELECT add_continuous_aggregate_policy('mv_balancing_summary',
            start_offset => INTERVAL '1 day',
            end_offset => INTERVAL '5 minutes',
            schedule_interval => INTERVAL '5 minutes')
        """))

        # Create supporting indexes on the materialized view
        connection.execute(sa.text("""
        CREATE INDEX ON mv_balancing_summary (interval DESC, network_id, network_region)
        """))

        connection.execute(sa.text("""
        CREATE INDEX ON mv_balancing_summary (network_id, network_region, interval DESC)
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
        SELECT remove_continuous_aggregate_policy('mv_balancing_summary')
        """))

        # Drop the materialized view
        connection.execute(sa.text("""
        DROP MATERIALIZED VIEW IF EXISTS mv_balancing_summary
        """))

    except Exception as e:
        print(f"Error in downgrade: {e}")
        raise
