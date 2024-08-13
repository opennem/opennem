"""
RecordReactor demand methods
"""

import logging
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import text

from opennem.core.units import get_unit
from opennem.db import SessionLocalAsync
from opennem.recordreactor.buckets import get_bucket_interval
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneMetric,
    MilestonePeriod,
    MilestoneRecordSchema,
    get_milestone_period_from_bucket_size,
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
    network: NetworkSchema, bucket_size: MilestonePeriod, start_date: datetime, end_date: datetime, region_group: bool = False
) -> list[MilestoneRecordSchema]:
    bucket_sql = get_bucket_interval(bucket_size, interval_size=network.interval_size)

    logger.info(f"Aggregating demand data for {network.code} bucket size {bucket_size} from {start_date}")

    query_network_region = "network_region," if region_group else ""
    group_by = "1,2,3" if region_group else "1,2"

    query = text(f"""
        SELECT
            time_bucket_gapfill('{bucket_sql}', interval) AS interval,
            network_id,
            {query_network_region}
            MIN(bs.demand_total) AS min_demand,
            MAX(bs.demand_total) AS max_demand,
            MIN(bs.price) AS min_price,
            MAX(bs.price) AS max_price
        FROM
            balancing_summary bs
        WHERE
            bs.network_id = :network_id AND
            bs.interval >= :start_date AND
            bs.interval < :end_date
        GROUP BY
            {group_by}
    """)

    async with SessionLocalAsync() as session:
        result = await session.execute(
            query,
            {
                "network_id": network.code,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        rows = result.fetchall()

    milestone_records: list[MilestoneRecordSchema] = []

    for row in rows:
        milestone_records.append(
            MilestoneRecordSchema(
                interval=row.interval,
                aggregate=MilestoneAggregate.low,
                metric=MilestoneMetric.demand,
                period=get_milestone_period_from_bucket_size(bucket_size),
                unit=get_unit("demand_mega"),
                network=network,
                network_region=row.network_region if region_group else None,
                value=row.min_demand,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=row.interval,
                aggregate=MilestoneAggregate.high,
                metric=MilestoneMetric.demand,
                period=get_milestone_period_from_bucket_size(bucket_size),
                unit=get_unit("demand_mega"),
                network=network,
                network_region=row.network_region if region_group else None,
                value=row.max_demand,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=row.interval,
                aggregate=MilestoneAggregate.low,
                metric=MilestoneMetric.price,
                period=get_milestone_period_from_bucket_size(bucket_size),
                unit=get_unit("market_value"),
                network=network,
                network_region=row.network_region if region_group else None,
                value=row.min_price,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=row.interval,
                aggregate=MilestoneAggregate.high,
                metric=MilestoneMetric.price,
                period=get_milestone_period_from_bucket_size(bucket_size),
                unit=get_unit("market_value"),
                network=network,
                network_region=row.network_region if region_group else None,
                value=row.max_price,
            )
        )

    return milestone_records


async def run_price_demand_milestone_for_interval(
    network: NetworkSchema, bucket_size: str, period_start: datetime, period_end: datetime
):
    milestone_data = await aggregate_demand_and_price_data(
        network=network,
        bucket_size=bucket_size,
        start_date=period_start,
        end_date=period_end,
        region_group=False,
    )

    await persist_milestones(
        milestones=milestone_data,
    )

    milestone_data = await aggregate_demand_and_price_data(
        network=network,
        bucket_size=bucket_size,
        start_date=period_start,
        end_date=period_end,
        region_group=True,
    )

    await persist_milestones(
        milestones=milestone_data,
    )
