"""
RecordReactor demand methods
"""

import asyncio
import itertools
import logging
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import text

from opennem.core.units import get_unit
from opennem.db import get_read_session
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestonePeriod,
    MilestoneRecordSchema,
    MilestoneType,
)
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.recordreactor.controllers.demand")


class MilestonesDemandPriceData(BaseModel):
    bucket: datetime
    network_region: str
    demand_low: float | None
    demand_high: float | None
    demand_sum: float | None
    price_low: float | None
    price_high: float | None
    price_sum: float | None


async def aggregate_demand_and_price_data(
    network: NetworkSchema, interval_date: datetime, region_group: bool = False
) -> list[MilestoneRecordSchema]:
    """
    Get demand and price data for a given interval and network


    """
    query_network_region = "network_region," if region_group else ""
    group_by = "1,2,3" if region_group else "1,2"

    query = text(f"""
        SELECT
            interval,
            network_id,
            {query_network_region}
            sum(bs.demand_total) as demand_total,
            avg(bs.price) as price
        FROM
            balancing_summary bs
        WHERE
            bs.network_id = :network_id AND
            bs.interval = :interval_date
        GROUP BY
            {group_by}
    """)

    async with get_read_session() as session:
        result = await session.execute(
            query,
            {
                "network_id": network.code,
                "interval_date": interval_date,
            },
        )

        rows = result.fetchall()

    milestone_records: list[MilestoneRecordSchema] = []

    for row in rows:
        for aggregate, metric in itertools.product(
            [MilestoneAggregate.low, MilestoneAggregate.high], [MilestoneType.demand_power, MilestoneType.price]
        ):
            milestone_records.append(
                MilestoneRecordSchema(
                    interval=row.interval,
                    aggregate=aggregate,
                    metric=metric,
                    period=MilestonePeriod.interval,
                    unit=get_unit("demand_mega") if metric == MilestoneType.demand_power else get_unit("price_energy_mega"),
                    network=network,
                    network_region=row.network_region if region_group else None,
                    fueltech=MilestoneFueltechGrouping.demand if metric == MilestoneType.demand_power else None,
                    value=row.price if metric == MilestoneType.price else row.demand_total,
                )
            )

    return milestone_records


async def run_price_demand_milestone_for_interval(network: NetworkSchema, bucket_size: MilestonePeriod, interval: datetime):
    if bucket_size != MilestonePeriod.interval:
        return

    async def _get_and_persist_milestone_data(region_group: bool):
        milestone_data = await aggregate_demand_and_price_data(
            network=network,
            interval_date=interval,
            region_group=region_group,
        )

        await persist_milestones(
            milestones=milestone_data,
        )

    tasks = []
    for region_group in [True, False]:
        tasks.append(_get_and_persist_milestone_data(region_group=region_group))

    if tasks:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    import asyncio

    from opennem.schema.network import NetworkNEM

    interval = datetime.fromisoformat("2024-05-01T00:00:00")

    asyncio.run(
        run_price_demand_milestone_for_interval(network=NetworkNEM, bucket_size=MilestonePeriod.interval, interval=interval)
    )
