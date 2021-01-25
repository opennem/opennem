# pylint: disable=no-member
"""
Create mv_nem_facility_power_30min

Revision ID: ec9daa4f407c
Revises: 66e98f534a41
Create Date: 2021-01-26 01:05:05.043919

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ec9daa4f407c"
down_revision = "66e98f534a41"
branch_labels = None
depends_on = None

stmt_drop = "drop materialized view if exists mv_nem_facility_power_30min cascade;"


stmt = """
CREATE MATERIALIZED VIEW mv_nem_facility_power_30min WITH (timescaledb.continuous) AS
select
    time_bucket('30 minutes', fs.trading_interval) as trading_interval,
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
