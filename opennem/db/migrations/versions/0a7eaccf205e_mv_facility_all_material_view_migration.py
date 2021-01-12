# pylint: disable=no-member
"""
mv_facility_all material view migration

Revision ID: 0a7eaccf205e
Revises: 43f1d539490f
Create Date: 2021-01-12 18:53:42.852651

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0a7eaccf205e"
down_revision = "43f1d539490f"
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
            f.network_region
        order by 1 desc;
    """
    )


def downgrade() -> None:
    op.execute("drop materialized view if exists mv_facility_all;")
