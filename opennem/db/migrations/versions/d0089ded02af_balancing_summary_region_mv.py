# pylint: disable=no-member
"""
Balancing summary region mv

Revision ID: d0089ded02af
Revises: 2f198fa45c76
Create Date: 2021-01-14 02:00:44.434001

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d0089ded02af"
down_revision = "2f198fa45c76"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
    drop view if exists mv_balancing_summary_region_hour cascade;

    CREATE OR REPLACE VIEW mv_balancing_summary_region_hour WITH (timescaledb.continuous) AS
    select
        time_bucket('1 hour', bs.trading_interval) as trading_interval,
        bs.network_id,
        bs.network_region,
        avg(bs.price) as price
    from balancing_summary bs
    group by
        1, 2, 3;

    """
    )


def downgrade() -> None:
    op.execute("drop view if exists mv_balancing_summary_region_hour cascade;")
