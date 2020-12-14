# pylint: disable=no-member
"""
Material view for energy outputs

Revision ID: 674d602ecf59
Revises: d8bd4db7c53d
Create Date: 2020-12-14 18:40:18.740870

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "674d602ecf59"
down_revision = "d8bd4db7c53d"
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
        energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated)) as energy
    from facility_scada fs
    group by
        1,
        fs.facility_code;
    """
    )


def downgrade() -> None:
    op.execute(
        """
    drop view if exists mv_facility_energy_hour cascade;
    """
    )
