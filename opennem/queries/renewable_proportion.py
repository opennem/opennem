"""
OpenNEM queries for renewable proportion

"""

from datetime import datetime

from sqlalchemy import case, func, literal_column, select, text
from sqlalchemy.sql import expression as sql

from opennem.db import get_read_session
from opennem.db.models.opennem import BalancingSummary, Facility, FacilityScada, FuelTech
from opennem.recordreactor.buckets import get_bucket_interval
from opennem.recordreactor.schema import MilestonePeriod
from opennem.schema.network import NetworkNEM, NetworkSchema


async def get_renewable_energy_proportion(
    network: NetworkSchema,
    bucket_size: MilestonePeriod,
    start_date: datetime,
    end_date: datetime,
    network_region: str | None = None,
    group_by_region: bool = True,
) -> list[dict]:
    """
    Get the renewable energy proportion for a given network region and date range


    """
    rooftop_networks = ["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"]

    # Subquery for generation_rooftop
    generation_rooftop = (
        select(
            func.time_bucket_gapfill(text("'5 min'"), FacilityScada.interval).label("interval"),
            Facility.network_region,
            func.locf(func.sum(FacilityScada.generated)).label("generation"),
        )
        .select_from(FacilityScada)
        .join(Facility, Facility.code == FacilityScada.facility_code)
        .join(FuelTech, FuelTech.code == Facility.fueltech_id)
        .where(
            Facility.network_id.in_(rooftop_networks),
            Facility.fueltech_id == "solar_rooftop",
            FacilityScada.interval >= start_date,
            FacilityScada.interval < end_date,
        )
        .group_by(text("1"), text("2"))
        .alias("generation_rooftop")
    )

    # Subquery for generation_renewable
    generation_renewable = (
        select(
            func.time_bucket_gapfill(text("'5 min'"), FacilityScada.interval).label("interval"),
            Facility.network_region,
            func.sum(FacilityScada.generated).label("generation"),
        )
        .select_from(FacilityScada)
        .join(Facility, Facility.code == FacilityScada.facility_code)
        .join(FuelTech, FuelTech.code == Facility.fueltech_id)
        .where(
            Facility.network_id.in_(["NEM", "AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"]),
            Facility.fueltech_id != "solar_rooftop",
            FuelTech.renewable.is_(True),
            FacilityScada.interval >= start_date,
            FacilityScada.interval < end_date,
        )
        .group_by(text("1"), text("2"))
        .alias("generation_renewable")
    )

    # Subquery for demand
    demand = (
        select(
            func.time_bucket_gapfill(text("'5 min'"), BalancingSummary.interval).label("interval"),
            BalancingSummary.network_region,
            func.locf(func.coalesce(func.max(BalancingSummary.demand_total), func.max(BalancingSummary.demand))).label(
                "demand_total"
            ),
        )
        .select_from(BalancingSummary)
        .where(
            BalancingSummary.network_id == "NEM",
            BalancingSummary.interval >= start_date,
            BalancingSummary.interval < end_date,
        )
        .group_by(text("1"), text("2"))
        .alias("demand")
    )

    # Main query
    bucket_size_sql = get_bucket_interval(bucket_size)

    query = (
        select(
            func.time_bucket(text(f"'{bucket_size_sql}'"), generation_renewable.c.interval).label("interval"),
            case((group_by_region, generation_renewable.c.network_region), else_=literal_column(f"'{network.code}'")).label(
                "network_region"
            ),
            func.round(func.max(generation_renewable.c.generation), 2).label("generation_renewable"),
            func.round(func.max(generation_rooftop.c.generation), 2).label("generation_rooftop"),
            func.round(func.avg(demand.c.demand_total), 2).label("demand_total"),
            case(
                (
                    func.sum(demand.c.demand_total) > 0,
                    func.round(
                        (
                            (
                                func.sum(generation_rooftop.c.generation)
                                + func.coalesce(func.sum(generation_renewable.c.generation), 0)
                            )
                            / (func.sum(demand.c.demand_total) + func.coalesce(func.sum(generation_rooftop.c.generation), 0))
                        )
                        * 100,
                        4,
                    ),
                ),
                else_=sql.null(),
            ).label("renewable_proportion"),
        )
        .select_from(generation_renewable)
        .join(
            generation_rooftop,
            (generation_rooftop.c.interval == generation_renewable.c.interval)
            & (generation_rooftop.c.network_region == generation_renewable.c.network_region),
        )
        .join(
            demand,
            (demand.c.interval == generation_renewable.c.interval)
            & (demand.c.network_region == generation_renewable.c.network_region),
        )
    )

    if network_region:
        query = query.where(demand.c.network_region == network_region)

    query = query.group_by(text("1"), text("2")).order_by(text("1"), text("2"))

    async with get_read_session() as session:
        result = await session.execute(query)
        rows = result.fetchall()

        # Create a list of dictionaries with column names as keys
        column_names = result.keys()
        return [dict(zip(column_names, row, strict=False)) for row in rows]


if __name__ == "__main__":
    import asyncio

    async def main():
        result = await get_renewable_energy_proportion(
            network=NetworkNEM, bucket_size=MilestonePeriod.month, start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 31)
        )
        print(result)

    asyncio.run(main())
