# pylint: disable=no-member
"""
Material view energy network

Revision ID: ae504bc24d95
Revises: 674d602ecf59
Create Date: 2020-12-14 19:09:27.495897

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae504bc24d95"
down_revision = "674d602ecf59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    drop view if exists mv_network_energy_hour cascade;

    CREATE OR REPLACE VIEW  mv_network_energy_hour WITH (timescaledb.continuous) AS
    select
        time_bucket('1 hour', fs.trading_interval) as trading_interval,
        fs.network_id,
        energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated)) as energy
    from facility_scada fs
    group by
        1,
        2;

    """
    )


def downgrade() -> None:
    op.execute("drop view if exists mv_network_energy_hour cascade;")
