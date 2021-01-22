# pylint: disable=no-member
"""
create vw_region_flow_emissions

Revision ID: 47b8cabac4bb
Revises: 6100cbbcaf7e
Create Date: 2021-01-22 16:31:27.280503

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "47b8cabac4bb"
down_revision = "6100cbbcaf7e"
branch_labels = None
depends_on = None


stmt_drop = "drop view if exists vw_region_flow_emissions;"

stmt = """
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
left join mv_region_emissions ef on ef.trading_interval = f.trading_interval and ef.network_region = f.network_region
left join mv_region_emissions et on et.trading_interval = f.trading_interval and et.network_region = f.interconnector_region_to
where
    f.interconnector is True
group by 1, 2, 3, flow_region, 5, 6, f.interconnector_region_to
order by trading_interval desc, flow_from asc, flow_to asc;
"""


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(stmt_drop)
        op.execute(stmt)


def downgrade() -> None:
    op.execute(stmt_drop)
