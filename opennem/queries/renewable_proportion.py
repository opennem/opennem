"""
OpenNEM queries for renewable proportion

"""

from datetime import datetime

from sqlalchemy import case, func, select, text
from sqlalchemy.sql import expression as sql

from opennem.db import get_read_session
from opennem.db.models.opennem import BalancingSummary, Facility, FacilityScada, FuelTech, FuelTechGroup
from opennem.recordreactor.buckets import get_bucket_interval
from opennem.recordreactor.schema import MilestonePeriod
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM, NetworkWEMDE
from opennem.utils.datatable import datatable_print


async def get_renewable_energy_proportion(
    network: NetworkSchema,
    bucket_size: MilestonePeriod,
    start_date: datetime,
    end_date: datetime,
    network_region: str | None = None,
    group_by_region: bool = True,
    group_by_fueltech: bool = False,
    group_by_renewable: bool = False,
) -> list[dict]:
    """
    Get the renewable energy proportion for a given network region and date range


    """
    rooftop_networks = ["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"]

    if network in [NetworkWEM, NetworkWEMDE]:
        rooftop_networks = ["APVI"]

    # one of group_by_fueltech or group_by_renewable must be true
    assert group_by_fueltech or group_by_renewable, "one of group_by_fueltech or group_by_renewable must be true"

    # Subquery for generation_rooftop
    generation_rooftop = (
        select(
            func.time_bucket_gapfill(text("'5 min'"), FacilityScada.interval).label("interval"),
            Facility.network_region,
            case((group_by_fueltech, text("'solar'")), else_=text("NULL")).label("fueltech_id"),
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
        .group_by(text("1"), text("2"), text("3"))
        .alias("generation_rooftop")
    )

    # Subquery for generation_renewable
    generation = (
        select(
            func.time_bucket_gapfill(text("'5 min'"), FacilityScada.interval).label("interval"),
            Facility.network_region,
            case(
                (group_by_fueltech, FuelTechGroup.code), else_=text("'renewables'") if group_by_renewable else text("NULL")
            ).label("fueltech_id"),
            func.sum(FacilityScada.generated).label("generation"),
        )
        .select_from(FacilityScada)
        .join(Facility, Facility.code == FacilityScada.facility_code)
        .join(FuelTech, FuelTech.code == Facility.fueltech_id)
        .join(FuelTechGroup, FuelTechGroup.code == FuelTech.fueltech_group_id)
        .where(
            Facility.network_id.in_(["NEM", "AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"]),
            Facility.fueltech_id != "solar_rooftop",
            FacilityScada.interval >= start_date,
            FacilityScada.interval < end_date,
        )
    )

    if group_by_renewable:
        generation = generation.where(FuelTech.renewable.is_(True))

    generation = generation.group_by(text("1"), text("2"), text("3")).alias("generation_renewable")

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
            func.time_bucket(text(f"'{bucket_size_sql}'"), generation.c.interval).label("interval"),
            case((group_by_region, generation.c.network_region), else_=sql.null()).label("network_region"),
            case(
                (group_by_fueltech, generation.c.fueltech_id),
                (group_by_renewable, text("'renewables'")),
                else_=sql.null(),
            ).label("fueltech_id"),
            func.round(func.max(generation.c.generation), 2).label("generation"),
            func.round(func.max(generation_rooftop.c.generation), 2).label("generation_rooftop"),
            func.round(func.avg(demand.c.demand_total), 2).label("demand_total"),
            case(
                (
                    func.sum(demand.c.demand_total) > 0,
                    func.round(
                        (
                            (
                                func.sum(generation_rooftop.c.generation)
                                if not group_by_fueltech
                                else 0 + func.coalesce(func.sum(generation.c.generation), 0)
                            )
                            / (func.sum(demand.c.demand_total) + func.coalesce(func.sum(generation_rooftop.c.generation), 0))
                        )
                        * 100,
                        4,
                    ),
                ),
                else_=sql.null(),
            ).label("proportion"),
        )
        .select_from(generation)
        .join(
            generation_rooftop,
            (generation_rooftop.c.interval == generation.c.interval)
            & (generation_rooftop.c.network_region == generation.c.network_region),
        )
        .join(
            demand,
            (demand.c.interval == generation.c.interval) & (demand.c.network_region == generation.c.network_region),
        )
    )

    if network_region:
        query = query.where(demand.c.network_region == network_region)

    query = query.group_by(text("1"), text("2"), text("3")).order_by(text("1"), text("2"), text("3"))

    async with get_read_session() as session:
        result = await session.execute(query)
        rows = result.fetchall()

        # Create a list of dictionaries with column names as keys
        column_names = result.keys()
        return [dict(zip(column_names, row, strict=False)) for row in rows]


if __name__ == "__main__":
    import asyncio

    async def main():
        results = await get_renewable_energy_proportion(
            network=NetworkNEM,
            bucket_size=MilestonePeriod.interval,
            start_date=datetime.fromisoformat("2024-08-01 12:00:00"),
            end_date=datetime.fromisoformat("2024-08-01 12:05:00"),
            group_by_region=True,
            group_by_fueltech=False,
            group_by_renewable=True,
        )
        datatable_print(results)

    asyncio.run(main())
