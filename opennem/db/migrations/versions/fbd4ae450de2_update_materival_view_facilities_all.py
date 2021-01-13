# pylint: disable=no-member
"""
Update materival view facilities_all to include
interconnector metadata

Revision ID: fbd4ae450de2
Revises: 0a7eaccf205e
Create Date: 2021-01-13 16:56:13.707337

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "fbd4ae450de2"
down_revision = "0a7eaccf205e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        drop materialized view if exists mv_facility_all;
        create materialized view mv_facility_all as
        select
            fs.trading_interval,
            f.code,
            f.fueltech_id,
            f.network_id,
            f.network_region,
            f.interconnector,
            f.interconnector_region_to,
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
        order by 1 desc;
    """
    )


def downgrade() -> None:
    pass
