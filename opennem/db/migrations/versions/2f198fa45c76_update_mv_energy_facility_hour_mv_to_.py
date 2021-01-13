# pylint: disable=no-member
"""
Update mv_energy_facility_hour mv to include network_id

Revision ID: 2f198fa45c76
Revises: fbd4ae450de2
Create Date: 2021-01-14 01:58:05.502904

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2f198fa45c76"
down_revision = "fbd4ae450de2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    drop view if exists mv_facility_energy_hour cascade;

    CREATE OR REPLACE VIEW mv_facility_energy_hour WITH (timescaledb.continuous) AS
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
