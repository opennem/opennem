# pylint: disable=no-member
"""
Material view NEM 5 minute facility power

Revision ID: b30e47defd26
Revises: 4569d3c0509e
Create Date: 2020-12-24 15:49:45.636162

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b30e47defd26"
down_revision = "4569d3c0509e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    drop materialized view if exists mv_nem_facility_power_5min cascade;

    CREATE MATERIALIZED VIEW mv_nem_facility_power_5min WITH (timescaledb.continuous) AS
    select
        time_bucket('5 minutes', fs.trading_interval) as trading_interval,
        fs.facility_code,
        max(fs.generated) as facility_power
    from facility_scada fs
    where fs.network_id = 'NEM'
    group by
        1,
        fs.facility_code;

    """
    )


def downgrade() -> None:
    op.execute("drop view mv_nem_facility_power_5min")
