"""
RecordReactor demand methods
"""

import logging
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import text

from opennem.db import SessionLocalAsync
from opennem.recordreactor.buckets import get_bucket_interval
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric
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
    network: NetworkSchema, bucket_size: str, start_date: datetime, end_date: datetime
) -> list[dict]:
    bucket_sql = get_bucket_interval(bucket_size, interval_size=network.interval_size)

    logger.info(f"Aggregating demand data bucket size {bucket_size} from {start_date} to {end_date}")

    query = text(f"""
        SELECT
            time_bucket_gapfill('{bucket_sql}', interval) AS interval,
            network_id,
            network_region,
            MIN(bs.demand_total) AS min_demand,
            MAX(bs.demand_total) AS max_demand,
            SUM(bs.demand_total) AS total_demand,
            MIN(bs.price) AS min_price,
            MAX(bs.price) AS max_price,
            SUM(bs.price) AS total_price
        FROM
            balancing_summary bs
        WHERE
            bs.network_id = :network_id AND
            bs.interval >= :start_date AND
            bs.interval < :end_date
        GROUP BY
            1,2,3
        ORDER BY
            network_id,
            network_region
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

    return [
        {
            "bucket": row.interval,
            "network_id": row.network_id,
            "network_region": row.network_region,
            "demand_low": row.min_demand,
            "demand_high": row.max_demand,
            "demand_sum": row.total_demand,
            "price_low": row.min_price,
            "price_high": row.max_price,
            "price_sum": row.total_price,
        }
        for row in rows
    ]


async def run_price_demand_milestone_for_interval(
    network: NetworkSchema, bucket_size: str, period_start: datetime, period_end: datetime
):
    aggregated_data = await aggregate_demand_and_price_data(
        network=network,
        bucket_size=bucket_size,
        start_date=period_start,
        end_date=period_end,
    )

    await persist_milestones(
        metrics=[MilestoneMetric.demand, MilestoneMetric.price],
        aggregates=[MilestoneAggregate.high, MilestoneAggregate.low],
        bucket_size=bucket_size,
        aggregated_data=aggregated_data,
    )
