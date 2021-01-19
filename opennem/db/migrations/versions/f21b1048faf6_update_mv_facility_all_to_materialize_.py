# pylint: disable=no-member
"""
Update mv_facility_all to materialize timezones and truncs

Revision ID: f21b1048faf6
Revises: 9ce2abfe97e8
Create Date: 2021-01-19 15:22:19.429719

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f21b1048faf6"
down_revision = "9ce2abfe97e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """drop materialized view if exists mv_facility_all;
create materialized view mv_facility_all as
select
    fs.trading_interval,
    f.code,
    f.fueltech_id,
    f.network_id,
    f.network_region,
    f.interconnector,
    f.interconnector_region_to,
    date_trunc('day', fs.trading_interval at time zone 'AEST') as ti_day_aest,
    date_trunc('month', fs.trading_interval at time zone 'AEST') as ti_month_aest,
    date_trunc('day', fs.trading_interval at time zone 'AWST') as ti_day_awst,
    date_trunc('month', fs.trading_interval at time zone 'AWST') as ti_month_awst,
    max(fs.energy) as energy,
    case when avg(bs.price) >= 0  and min(fs.energy) >= 0 then
        coalesce(
            max(fs.energy) * avg(bs.price),
            0.0
        )
    else 0.0
    end as market_value,
    case when avg(f.emissions_factor_co2) >= 0  and min(fs.energy) >= 0 then
        coalesce(
            max(fs.energy) * avg(f.emissions_factor_co2),
            0.0
        )
    else 0.0
    end as emissions
from mv_facility_energy_hour fs
    left join facility f on fs.facility_code = f.code
    left join balancing_summary bs on
        bs.trading_interval = fs.trading_interval
        and bs.network_id=f.network_id
        and bs.network_region = f.network_region
where
    f.fueltech_id is not null
group by
    1,
    f.code,
    f.fueltech_id,
    f.network_id,
    f.network_region,
    f.interconnector,
    f.interconnector_region_to
order by 1 desc;"""
    )


def downgrade() -> None:
    pass
