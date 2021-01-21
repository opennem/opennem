# pylint: disable=no-member
"""
create mv_interchange_power_nem_region

Revision ID: 4c35e2483eb7
Revises: d130be833a0c
Create Date: 2021-01-22 00:42:41.261473

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "4c35e2483eb7"
down_revision = "d130be833a0c"
branch_labels = None
depends_on = None

stmt_drop = "drop materialized view if exists mv_interchange_power_nem_region cascade;"

stmt = """
    CREATE MATERIALIZED VIEW mv_interchange_power_nem_region WITH (timescaledb.continuous) AS
    select
        time_bucket(INTERVAL '5 minutes', bs.trading_interval) as trading_interval,
        bs.network_id,
        bs.network_region,
        case when avg(bs.net_interchange) < 0 then
            avg(bs.net_interchange)
        else 0
        end as imports,
        case when avg(bs.net_interchange) > 0 then
            avg(bs.net_interchange)
        else 0
        end as exports
    from balancing_summary bs
    group by 1, 2, 3;
"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(stmt_drop)
        op.execute(stmt)


def downgrade() -> None:
    op.execute(stmt_drop)
