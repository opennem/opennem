# pylint: disable=no-member
"""
Update mv_facility_energy_hour

Revision ID: 7af7a611233f
Revises: f7e87ce05302
Create Date: 2021-01-26 02:16:21.958133

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "7af7a611233f"
down_revision = "f7e87ce05302"
branch_labels = None
depends_on = None


stmt_drop = "drop materialized view if exists mv_facility_energy_hour cascade;"


stmt = """
CREATE MATERIALIZED VIEW mv_facility_energy_hour WITH (timescaledb.continuous) AS
select
    time_bucket('1 hour', fs.trading_interval) as trading_interval,
    fs.facility_code,
    fs.network_id,
    energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated)) as energy
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
