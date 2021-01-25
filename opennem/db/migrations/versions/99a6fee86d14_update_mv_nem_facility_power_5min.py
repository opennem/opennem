# pylint: disable=no-member
"""
Update mv_nem_facility_power_5min

Revision ID: 99a6fee86d14
Revises: 16d3da9550b7
Create Date: 2021-01-26 01:57:44.846831

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "99a6fee86d14"
down_revision = "16d3da9550b7"
branch_labels = None
depends_on = None


stmt_drop = "drop materialized view if exists mv_nem_facility_power_5min cascade;"


stmt = """
CREATE MATERIALIZED VIEW mv_nem_facility_power_5min WITH (timescaledb.continuous) AS
select
    time_bucket('5 minutes', fs.trading_interval) as trading_interval,
    fs.facility_code,
    avg(fs.generated) as facility_power,
    fs.is_forecast
from facility_scada fs
where fs.network_id = 'NEM' and trading_interval > '2021-01-01 00:00:00+10'
group by
    1,
    fs.facility_code,
    fs.is_forecast;

"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(stmt_drop)
        op.execute(stmt)


def downgrade() -> None:
    op.execute(stmt_drop)
