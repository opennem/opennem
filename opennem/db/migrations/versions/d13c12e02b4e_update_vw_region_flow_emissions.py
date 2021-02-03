# pylint: disable=no-member
"""
Update vw_region_flow_emissions

Revision ID: d13c12e02b4e
Revises: 4503ef797f3a
Create Date: 2021-01-28 01:00:02.168088

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d13c12e02b4e"
down_revision = "4503ef797f3a"
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

stmt_drop2 = "drop view if exists vw_region_flow_emissions;"

stmt2 = """
create view vw_region_flow_emissions as select
    f.trading_interval at time zone 'AEST' as trading_interval,
    date_trunc('day', f.trading_interval) at time zone 'AEST' as ti_day_aest,
    date_trunc('month', f.trading_interval) at time zone 'AEST' as ti_month_aest,
    sum(f.energy) as flow_energy,
    f.network_region || '->' || f.interconnector_region_to as flow_region,
    f.network_region as flow_from,
    f.interconnector_region_to as flow_to,
    abs(sum(ef.emissions_per_kw) * sum(f.energy)) as flow_from_emissions,
    abs(sum(et.emissions_per_kw) * sum(f.energy)) as flow_to_emissions
from mv_facility_all f
left join mv_region_emissions ef on
    ef.trading_interval = f.trading_interval and
    ef.network_region = f.network_region
left join mv_region_emissions et on
    et.trading_interval = f.trading_interval and
    et.network_region = f.interconnector_region_to
where
    f.interconnector is True
group by 1, 2, 3, flow_region, 5, 6, f.interconnector_region_to
order by trading_interval desc, flow_from asc, flow_to asc;
"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(stmt_drop)
        op.execute(stmt)
        op.execute(stmt_drop2)
        op.execute(stmt2)


def downgrade() -> None:
    op.execute(stmt_drop)
    op.execute(stmt_drop2)
