"""
RecordReactor demand methods
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, text

from opennem import settings
from opennem.db import AsyncSession, SessionLocal
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneType
from opennem.recordreactor.utils.buckets import BUCKET_SIZES, get_bucket_sql, get_period_start_end, is_end_of_period
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import get_last_completed_interval_for_network, make_aware_for_network

logger = logging.getLogger("opennem.recordreactor.controllers.demand")


async def aggregate_demand_and_price_data(
    session: AsyncSession, network_id: str, bucket_size: str, start_date: datetime, end_date: datetime
) -> list[dict]:
    bucket_sql = get_bucket_sql(bucket_size)

    logger.info(f"Aggregating demand data for {network_id} bucket size {bucket_size} from {start_date} to {end_date}")

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
            AVG(demand_total) AS avg_demand,
            SUM(demand_total) AS total_demand,
            MIN(price) AS min_price,
            MAX(price) AS max_price,
            AVG(price) AS avg_price,
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
            "network_id": network_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    rows = result.fetchall()

    return [
        {
            "bucket": row.bucket,
            "network_region": row.network_region,
            "min_demand": row.min_demand,
            "max_demand": row.max_demand,
            "avg_demand": row.avg_demand,
            "total_demand": row.total_demand,
            "min_price": row.min_price,
            "max_price": row.max_price,
            "avg_price": row.avg_price,
            "total_price": row.total_price,
        }
        for row in rows
    ]


async def persist_demand_and_price_milestones(session, network_id: str, bucket_size: str, aggregated_data: list[dict]):
    for data in aggregated_data:
        demand_high_milestone_id = f"au.{network_id.lower()}.{data['network_region'].lower()}.demand.high.{bucket_size}"
        demand_low_milestone_id = f"au.{network_id.lower()}.{data['network_region'].lower()}.demand.low.{bucket_size}"
        price_high_milestone_id = f"au.{network_id.lower()}.{data['network_region'].lower()}.price.high.{bucket_size}"
        price_low_milestone_id = f"au.{network_id.lower()}.{data['network_region'].lower()}.price.low.{bucket_size}"

        # Query for existing milestones with max and min values
        demand_high_milestone = await session.execute(
            select(Milestones).where(Milestones.record_id == demand_high_milestone_id).order_by(Milestones.value.desc()).limit(1)
        )
        demand_high_milestone = demand_high_milestone.scalar_one_or_none()

        demand_low_milestone = await session.execute(
            select(Milestones).where(Milestones.record_id == demand_low_milestone_id).order_by(Milestones.value.asc()).limit(1)
        )
        demand_low_milestone = demand_low_milestone.scalar_one_or_none()

        price_high_milestone = await session.execute(
            select(Milestones).where(Milestones.record_id == price_high_milestone_id).order_by(Milestones.value.desc()).limit(1)
        )
        price_high_milestone = price_high_milestone.scalar_one_or_none()

        price_low_milestone = await session.execute(
            select(Milestones).where(Milestones.record_id == price_low_milestone_id).order_by(Milestones.value.asc()).limit(1)
        )
        price_low_milestone = price_low_milestone.scalar_one_or_none()

        if not demand_high_milestone or (
            data["max_demand"] and data["max_demand"] > demand_high_milestone.value and demand_high_milestone.value > 0
        ):
            demand_high_milestone = Milestones(
                record_id=demand_high_milestone_id,
                interval=data["bucket"],
                record_type=MilestoneType.high,
                significance=1,
                value=data["max_demand"],
                network_id=network_id,
                network_region=data["network_region"],
                period=bucket_size,
                description=f"Highest {bucket_size} demand for {data['network_region']} in {network_id}. ",
                record_field="demand",
                previous_record_id=demand_high_milestone.instance_id if demand_high_milestone else None,
            )

            await session.merge(demand_high_milestone)

            logger.info(
                f"Added milestone for interval {data['bucket']} {demand_high_milestone_id} with value {data['max_demand']}"
            )

        if not demand_low_milestone or (
            data["min_demand"] and data["min_demand"] < demand_low_milestone.value and demand_low_milestone.value > 0
        ):
            demand_low_milestone = Milestones(
                record_id=demand_low_milestone_id,
                interval=data["bucket"],
                record_type=MilestoneType.low,
                significance=1,
                value=data["min_demand"],
                network_id=network_id,
                network_region=data["network_region"],
                period=bucket_size,
                description=f"Lowest {bucket_size} demand for {data['network_region']} in {network_id}. ",
                record_field="demand",
                previous_record_id=demand_low_milestone.instance_id if demand_low_milestone else None,
            )

            await session.merge(demand_low_milestone)

            logger.info(
                f"Added milestone for interval {data['bucket']} {demand_low_milestone_id} with value {data['max_demand']}"
            )

        if not price_low_milestone or (
            data["min_price"] and data["min_price"] < price_low_milestone.value and price_low_milestone.value
        ):
            price_low_milestone = Milestones(
                record_id=price_low_milestone_id,
                interval=data["bucket"],
                record_type=MilestoneType.low,
                significance=1,
                value=data["min_price"],
                network_id=network_id,
                network_region=data["network_region"],
                period=bucket_size,
                description=f"Lowest {bucket_size} price for{data['network_region']} in {network_id}.",
                previous_record_id=price_low_milestone.instance_id if price_low_milestone else None,
                record_field="price",
            )

            await session.merge(price_low_milestone)

            logger.info(f"Added milestone for interval {data['bucket']} {price_low_milestone_id} with value {data['min_price']}")

        if not price_high_milestone or (
            data["max_price"] and data["max_price"] > price_high_milestone.value and price_high_milestone.value > 0
        ):
            price_high_milestone = Milestones(
                record_id=price_high_milestone_id,
                interval=data["bucket"],
                record_type=MilestoneType.high,
                significance=1,
                value=data["max_price"],
                network_id=network_id,
                network_region=data["network_region"],
                period=bucket_size,
                description=f"Highest {bucket_size} price for {data['network_region']} in {network_id}.",
                previous_record_id=price_high_milestone.instance_id if price_high_milestone else None,
                record_field="price",
            )

            await session.merge(price_high_milestone)

            logger.info(f"Added milestone for interval {data['bucket']} {price_high_milestone_id} with value {data['max_price']}")

    await session.flush()


async def run_price_demand_milestone_for_interval(
    network: NetworkSchema, bucket_size: str, period_start: datetime, period_end: datetime
):
    async with SessionLocal() as session:
        aggregated_data = await aggregate_demand_and_price_data(
            session=session,
            network_id=network.code,
            bucket_size=bucket_size,
            start_date=period_start,
            end_date=period_end,
        )

        await persist_demand_and_price_milestones(
            session=session,
            network_id=network.code,
            bucket_size=bucket_size,
            aggregated_data=aggregated_data,
        )

        await session.commit()


async def run_milestone_demand(start_interval: datetime, end_interval: datetime | None = None):
    num_tasks = 10

    for network in [NetworkNEM, NetworkWEM]:
        if not network.interval_size:
            continue

        logger.info(f"Processing price and demand milestone data network {network.code}")

        if not end_interval:
            end_interval = get_last_completed_interval_for_network(network)

        start_interval = make_aware_for_network(start_interval, network)
        end_interval = make_aware_for_network(end_interval, network)

        current_interval = start_interval
        tasks = []

        while current_interval <= end_interval:
            # Process each bucket size for this interval
            for bucket_size in BUCKET_SIZES:
                if is_end_of_period(current_interval, bucket_size):
                    period_start, period_end = get_period_start_end(current_interval, bucket_size)

                    if not settings.dry_run:
                        task = run_price_demand_milestone_for_interval(
                            network=network,
                            bucket_size=bucket_size,
                            period_start=period_start,
                            period_end=period_end,
                        )
                        tasks.append(task)

            # Move to the next interval
            current_interval += timedelta(minutes=network.interval_size)

            if len(tasks) >= num_tasks:  # Adjust this number based on your system's capabilities
                await asyncio.gather(*tasks)
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)


# Usage
if __name__ == "__main__":
    import asyncio

    asyncio.run(run_milestone_demand(start_interval=datetime.fromisoformat("2024-01-01T00:00:00+10:00")))

    # Uncomment to run full backfill
    # backfill_demand_milestones(engine)

    # Process new data
    # asyncio.run(process_new_balancing_summary())
