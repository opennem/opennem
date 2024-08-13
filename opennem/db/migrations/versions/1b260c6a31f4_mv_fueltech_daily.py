# pylint: disable=no-member
"""
mv_fueltech_daily

Revision ID: 1b260c6a31f4
Revises: 3ad9745a5bd0
Create Date: 2024-08-13 21:02:32.225104

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "1b260c6a31f4"
down_revision = "3ad9745a5bd0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_fueltech_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', fs.interval) AS trading_day,
            fs.network_id,
            f.network_region,
            f.fueltech_id AS fueltech_code,
            round(sum(fs.generated), 4) as generated,
            round(sum(fs.energy), 4) as energy,
            CASE
                WHEN sum(fs.energy) > 0 THEN round(sum(f.emissions_factor_co2 * fs.energy), 4)
                ELSE 0
            END AS emissions,
            CASE
                WHEN sum(fs.energy) > 0 THEN round(sum(f.emissions_factor_co2 * fs.energy) / sum(fs.energy), 4)
                ELSE 0
            END AS emissions_intensity
        FROM
            facility_scada fs
            JOIN facility f ON fs.facility_code = f.code
        WHERE
            fs.is_forecast IS FALSE AND
            f.fueltech_id IS NOT NULL AND
            f.fueltech_id NOT IN ('imports', 'exports', 'interconnector')
        GROUP BY
            1, 2, 3, 4
        ORDER BY
            1 DESC, 2, 3, 4;
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy('mv_fueltech_daily',
            start_offset => NULL,
            end_offset => INTERVAL '1 h',
            schedule_interval => INTERVAL '1 h');
    """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW mv_fueltech_daily CASCADE;")
