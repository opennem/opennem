# pylint: disable=no-member
"""
mv_facilities_all update mv_facilities_all with new balancing
summary mv

Revision ID: 98e2968b63e4
Revises: d0089ded02af
Create Date: 2021-01-14 06:27:10.956571

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "98e2968b63e4"
down_revision = "d0089ded02af"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        drop materialized view if exists mv_facility_all;
        create materialized view mv_facility_all as
        select
            time_bucket_gapfill('1 hour', fs.trading_interval) as trading_interval,
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
            left join mv_balancing_summary_region_hour bs on
                fs.trading_interval = bs.trading_interval and
                fs.network_id = bs.network_id and
                bs.network_region = f.network_region
        where
            f.fueltech_id is not null and
            fs.trading_interval <= now() and
            fs.trading_interval > '1900-01-01'
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
