"""
RecordReactor demand methods
"""

import logging
from datetime import datetime
from itertools import product

from sqlalchemy import text

from opennem.db import AsyncSession, SessionLocal
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.buckets import get_bucket_sql
from opennem.recordreactor.map import get_milestone_map_by_record_id
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric, MilestoneRecord, MilestoneSchema
from opennem.recordreactor.state import get_current_milestone_state
from opennem.recordreactor.utils import check_milestone_is_new
from opennem.schema.network import NetworkSchema
from opennem.utils.dates import make_aware_for_network

logger = logging.getLogger("opennem.recordreactor.controllers.demand")


async def aggregate_demand_and_price_data(
    session: AsyncSession, network: NetworkSchema, bucket_size: str, start_date: datetime, end_date: datetime
) -> list[dict]:
    bucket_sql = get_bucket_sql(bucket_size)

    logger.info(f"Aggregating demand data for {network} bucket size {bucket_size} from {start_date} to {end_date}")

    query = text(f"""
        WITH time_zone_data AS (
            SELECT
                {bucket_sql} AS bucket,
                network_region,
                demand_total,
                price
            FROM
                balancing_summary
            WHERE
                network_id = :network_id
                AND trading_interval BETWEEN :start_date AND :end_date
        )
        SELECT
            :start_date AS bucket,
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
            network_region
        ORDER BY
            network_region
    """)

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
            "bucket": row.bucket,
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


async def persist_demand_and_price_milestones(session, network: NetworkSchema, bucket_size: str, aggregated_data: list[dict]):
    """
    Persists the demand and price milestones for the given network and bucket size

    Args:
        session (AsyncSession): The database session
        network_id (str): The network ID
        bucket_size (str): The bucket size
        aggregated_data (list[dict]): The aggregated data

    Returns:
        None

    """

    milestone_state = await get_current_milestone_state()

    for data in aggregated_data:
        # create mileston schemas
        milestone_schemas: list[MilestoneSchema] = []

        for metric, aggregate in product(
            [MilestoneMetric.demand, MilestoneMetric.price], [MilestoneAggregate.high, MilestoneAggregate.low]
        ):
            milestone_map = await get_milestone_map_by_record_id(
                f"au.{network.code.lower()}.{data['network_region'].lower()}.{metric.value}.{bucket_size}.{aggregate.value}"
            )
            milestone_schemas.append(milestone_map)

        for milestone_schema in milestone_schemas:
            milestone_prev: MilestoneRecord | None = None

            if milestone_schema.record_id in milestone_state:
                milestone_prev = milestone_state[milestone_schema.record_id]

            if not milestone_prev or check_milestone_is_new(milestone_schema, milestone_prev, data):
                data_key = f"{milestone_schema.metric.value}_{milestone_schema.aggregate.value}"
                data_value = data.get(data_key)

                bucket = data.get("bucket")

                if not bucket:
                    raise ValueError(f"No bucket data for {milestone_schema.record_id}")

                interval = make_aware_for_network(bucket, network)

                milestone_new = Milestones(
                    record_id=milestone_schema.record_id,
                    interval=interval,
                    aggregate=milestone_schema.aggregate.value,
                    metric=milestone_schema.metric.value,
                    period=bucket_size,
                    significance=1,
                    value=data_value,
                    value_unit=milestone_schema.value_unit.value,
                    network_id=network.code,
                    network_region=data.get("network_region"),
                    previous_record_id=milestone_prev.instance_id if milestone_prev else None,
                )

                await session.merge(milestone_new)

                # update state to point to this new milestone
                milestone_state[milestone_schema.record_id] = milestone_new

                logger.info(f"Added milestone for interval {data['bucket']} {milestone_schema.record_id} with value {data_value}")

    await session.flush()


async def run_price_demand_milestone_for_interval(
    network: NetworkSchema, bucket_size: str, period_start: datetime, period_end: datetime
):
    async with SessionLocal() as session:
        aggregated_data = await aggregate_demand_and_price_data(
            session=session,
            network=network,
            bucket_size=bucket_size,
            start_date=period_start,
            end_date=period_end,
        )

        await persist_demand_and_price_milestones(
            session=session,
            network=network,
            bucket_size=bucket_size,
            aggregated_data=aggregated_data,
        )

        await session.commit()
