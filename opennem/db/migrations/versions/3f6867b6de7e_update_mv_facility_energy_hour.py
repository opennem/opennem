# pylint: disable=no-member
"""
Update mv_facility_energy_hour

Revision ID: 3f6867b6de7e
Revises: 9c7482a0fc9a
Create Date: 2021-01-19 17:11:21.222167

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "3f6867b6de7e"
down_revision = "9c7482a0fc9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    drop view if exists mv_facility_energy_hour cascade;

    CREATE OR REPLACE VIEW mv_facility_energy_hour WITH (timescaledb.continuous, timescaledb.refresh_interval = '1h', timescaledb.refresh_lag='1h') AS
    select
        time_bucket('1 hour', fs.trading_interval) as trading_interval,
        fs.facility_code,
        fs.network_id,
        energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated)) as energy
    from facility_scada fs
    group by
        1, 2, 3;
    """
    )


def downgrade() -> None:
    pass
