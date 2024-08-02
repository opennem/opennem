"""
RecordReactor generation methods
"""

import logging
from datetime import datetime
from itertools import product

from sqlalchemy import text

from opennem.db import AsyncSession, SessionLocal
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.buckets import get_bucket_sql
from opennem.recordreactor.map import get_milestone_map_by_record_id
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric, MilestoneRecord
from opennem.recordreactor.state import get_current_milestone_state
from opennem.recordreactor.utils import check_milestone_is_new
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.recordreactor.controllers.generation")


async def aggregate_generation_and_emissions_data(
    session: AsyncSession, network_id: str, bucket_size: str, start_date: datetime, end_date: datetime
) -> list[dict]:
    bucket_sql = get_bucket_sql(bucket_size, extra="AT TIME ZONE 'Australia/Brisbane'")

    logger.info(
        f"Aggregating generation and emissions data for {network_id} bucket size {bucket_size} from {start_date} to {end_date}"
    )

    query = text(f"""
        WITH timezone_data AS (
            SELECT 'Australia/Brisbane'::text AS timezone
        )
        SELECT
            {bucket_sql} AS trading_interval,
            f.network_region,
            ft.code AS fueltech_code,
            sum(fs.generated) as fueltech_generated,
            sum(fs.generated * n.interval_size / 60.0) AS fueltech_energy,
            CASE
                WHEN sum(fs.generated) > 0 THEN sum(f.emissions_factor_co2 * fs.generated * n.interval_size / 60.0)
                ELSE 0
            END AS fueltech_emissions,
            CASE
                WHEN sum(fs.generated) > 0 THEN
                    round(
                        sum(f.emissions_factor_co2 * fs.generated * n.interval_size / 60.0) /
                        sum(fs.generated * n.interval_size / 60.0), 4
                    )
                ELSE 0
            END AS fueltech_emissions_intensity
        FROM
            facility_scada fs
            JOIN facility f ON fs.facility_code = f.code
            JOIN fueltech ft ON f.fueltech_id = ft.code
            JOIN network n ON f.network_id = n.code
            CROSS JOIN timezone_data tz
        WHERE
            fs.is_forecast IS FALSE AND
            f.fueltech_id IS NOT NULL AND
            f.fueltech_id NOT IN ('imports', 'exports', 'interconnector') AND
            f.network_id IN ('NEM', 'AEMO_ROOFTOP', 'AEMO_ROOFTOP_BACKFILL') AND
            fs.trading_interval >= :date_start::timestamp AT TIME ZONE tz.timezone AND
            fs.trading_interval < :date_end::timestamp AT TIME ZONE tz.timezone
        GROUP BY
            1, 2, 3
        ORDER BY
            1 DESC, 2, 3;
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
            "generation_low": row.min_generation,
            "generation_high": row.max_generation,
            "generation_sum": row.total_generation,
            "emissions_low": row.min_emissions,
            "emissions_high": row.max_emissions,
            "emissions_sum": row.total_emissions,
        }
        for row in rows
    ]


async def persist_generation_milestones(session, network_id: str, bucket_size: str, aggregated_data: list[dict]):
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
        milestone_schemas = []

        for metric, aggregate in product(
            [MilestoneMetric.energy, MilestoneMetric.emissions, MilestoneMetric.power],
            [MilestoneAggregate.high, MilestoneAggregate.low],
        ):
            milestone_map = await get_milestone_map_by_record_id(
                f"au.{network_id.lower()}.{data['network_region'].lower()}.{metric.value}.{bucket_size}.{aggregate.value}"
            )
            milestone_schemas.append(milestone_map)

        for milestone_schema in milestone_schemas:
            milestone_prev: MilestoneRecord | None = None

            if milestone_schema.record_id in milestone_state:
                milestone_prev = milestone_state[milestone_schema.record_id]

            if not milestone_prev or check_milestone_is_new(milestone_schema, milestone_prev, data):
                data_key = f"{milestone_schema.metric.value}_{milestone_schema.aggregate.value}"
                data_value = data.get(data_key)

                milestone_new = Milestones(
                    record_id=milestone_schema.record_id,
                    interval=data.get("bucket"),
                    aggregate=milestone_schema.aggregate.value,
                    metric=milestone_schema.metric.value,
                    period=bucket_size,
                    significance=1,
                    value=data_value,
                    value_unit=milestone_schema.value_unit.value,
                    network_id=network_id,
                    network_region=data.get("network_region"),
                    previous_record_id=milestone_prev.instance_id if milestone_prev else None,
                )

                await session.merge(milestone_new)

                # update state to point to this new milestone
                milestone_state[milestone_schema.record_id] = milestone_new

                logger.info(f"Added milestone for interval {data['bucket']} {milestone_schema.record_id} with value {data_value}")

    await session.flush()


async def run_fueltech_generation_milestone_for_interval(
    network: NetworkSchema, bucket_size: str, period_start: datetime, period_end: datetime
):
    async with SessionLocal() as session:
        aggregated_data = await aggregate_generation_and_emissions_data(
            session=session,
            network_id=network.code,
            bucket_size=bucket_size,
            start_date=period_start,
            end_date=period_end,
        )

        await persist_generation_milestones(
            session=session,
            network_id=network.code,
            bucket_size=bucket_size,
            aggregated_data=aggregated_data,
        )

        await session.commit()
