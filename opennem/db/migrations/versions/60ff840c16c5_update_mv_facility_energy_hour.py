# pylint: disable=no-member
"""
Update mv_facility_energy_hour

Revision ID: 60ff840c16c5
Revises: 31ea8ecdfa44
Create Date: 2021-02-02 02:05:14.944479

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "60ff840c16c5"
down_revision = "31ea8ecdfa44"
branch_labels = None
depends_on = None

stmt_drop = "drop materialized view if exists mv_facility_energy_hour cascade;"


stmt = """
CREATE MATERIALIZED VIEW mv_facility_energy_hour WITH (timescaledb.continuous) AS
select
    time_bucket('1 hour', fs.trading_interval) as trading_interval,
    fs.facility_code,
    fs.network_id,
    (case
        when count(fs.eoi_quantity) > 0 then sum(fs.eoi_quantity)
        else energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated))
    end) as energy
from facility_scada fs
where fs.is_forecast is False
group by
    1, 2, 3;
"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(stmt_drop)
        op.execute(stmt)


def downgrade() -> None:
    op.execute(stmt_drop)
