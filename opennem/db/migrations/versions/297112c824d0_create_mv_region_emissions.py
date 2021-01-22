# pylint: disable=no-member
"""
create mv_region_emissions

Revision ID: 297112c824d0
Revises: 92c01037492d
Create Date: 2021-01-22 16:12:40.441310

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "297112c824d0"
down_revision = "92c01037492d"
branch_labels = None
depends_on = None

stmt_drop = "drop materialized view if exists mv_region_emissions;"

stmt = """
create materialized view mv_region_emissions as select
    f.trading_interval,
    f.network_region,
    case
        when sum(f.energy) > 0 then
            sum(f.emissions) / sum(f.energy)
        else 0
    end as emissions_per_kw
from mv_facility_all f
group by 1, f.network_region
order by 1 desc;
"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(stmt_drop)
        op.execute(stmt)


def downgrade() -> None:
    op.execute(stmt_drop)
