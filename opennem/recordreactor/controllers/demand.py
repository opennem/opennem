"""
RecordReactor demand methods
"""

import logging
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import text

from opennem.db import AsyncSession, SessionLocal
from opennem.recordreactor.buckets import get_bucket_sql
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric

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
    session: AsyncSession, bucket_size: str, start_date: datetime, end_date: datetime
) -> list[dict]:
    bucket_sql = get_bucket_sql(bucket_size)

    logger.info(f"Aggregating demand data bucket size {bucket_size} from {start_date} to {end_date}")

    query = text(f"""
        WITH time_zone_data AS (
            SELECT
                {bucket_sql} AS bucket,
                network_id,
                network_region,
                demand_total,
                price
            FROM
                balancing_summary
            WHERE
                trading_interval BETWEEN :start_date AND :end_date
        )
        SELECT
            :start_date AS bucket,
            network_id,
            network_region,
            MIN(demand_total) AS min_demand,
            MAX(demand_total) AS max_demand,
            SUM(demand_total) AS total_demand,
            MIN(price) AS min_price,
            MAX(price) AS max_price,
            SUM(price) AS total_price
        FROM
            time_zone_data
        GROUP BY
            network_id, network_region
        ORDER BY
            network_region
    """)

    result = await session.execute(
        query,
        {
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    rows = result.fetchall()

    return [
        {
            "bucket": row.bucket,
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


async def run_price_demand_milestone_for_interval(bucket_size: str, period_start: datetime, period_end: datetime):
    async with SessionLocal() as session:
        aggregated_data = await aggregate_demand_and_price_data(
            session=session,
            bucket_size=bucket_size,
            start_date=period_start,
            end_date=period_end,
        )

        await persist_milestones(
            session=session,
            metrics=[MilestoneMetric.demand, MilestoneMetric.price],
            aggregates=[MilestoneAggregate.high, MilestoneAggregate.low],
            bucket_size=bucket_size,
            aggregated_data=aggregated_data,
        )

        await session.commit()
