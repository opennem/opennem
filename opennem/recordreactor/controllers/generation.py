"""
RecordReactor generation methods
"""

import logging
from datetime import datetime

from sqlalchemy import text

from opennem.core.networks import network_from_network_code
from opennem.db import AsyncSession, SessionLocal
from opennem.recordreactor.buckets import get_bucket_sql
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.recordreactor.controllers.generation")


async def aggregate_generation_and_emissions_data(
    session: AsyncSession,
    network_id: str,
    bucket_size: str,
    start_date: datetime,
    end_date: datetime,
    fueltech_group: bool = True,
) -> list[dict]:
    timezone = network_from_network_code(network_id).timezone

    bucket_sql = get_bucket_sql(bucket_size, extra=f"AT TIME ZONE '{timezone}'")

    fueltech_id_column, fueltech_id_select = "", ""

    if fueltech_group:
        fueltech_id_select = "ftg.code AS fueltech_id,"
        fueltech_id_column = ", 4"

    logger.info(f"Aggregating generation & emissions data for {network_id} bucket size {bucket_size} for {start_date}")

    query = text(f"""
        WITH timezone_data AS (
            SELECT '{timezone}'::text AS timezone
        )
        SELECT
            {bucket_sql} AS trading_interval,
            f.network_id,
            f.network_region,
            {fueltech_id_select}
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
            JOIN fueltech_group ftg ON ft.fueltech_group_id = ftg.code
            JOIN network n ON f.network_id = n.code
            CROSS JOIN timezone_data tz
        WHERE
            fs.is_forecast IS FALSE AND
            f.fueltech_id IS NOT NULL AND
            f.fueltech_id NOT IN ('imports', 'exports', 'interconnector') AND
            f.network_id IN ('NEM', 'AEMO_ROOFTOP', 'AEMO_ROOFTOP_BACKFILL') AND
            fs.trading_interval >= :start_date AT TIME ZONE tz.timezone AND
            fs.trading_interval < :end_date AT TIME ZONE tz.timezone
        GROUP BY
            1, 2, 3{fueltech_id_column}
        ORDER BY
            1 DESC, 2, 3, 4;
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
            "bucket": row.trading_interval,
            "network_id": row.network_id if row.network_id not in ["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"] else "NEM",
            "network_region": row.network_region,
            "fueltech_id": row.fueltech_id if fueltech_group else None,
            "power_low": row.fueltech_generated,
            "power_high": row.fueltech_generated,
            "energy_low": row.fueltech_energy,
            "energy_high": row.fueltech_energy,
            "emissions_low": row.fueltech_emissions,
            "emissions_high": row.fueltech_emissions,
        }
        for row in rows
    ]


async def run_generation_energy_emissions_milestones(
    network: NetworkSchema, bucket_size: str, period_start: datetime, period_end: datetime, fueltech_group: bool = True
):
    async with SessionLocal() as session:
        aggregated_data = await aggregate_generation_and_emissions_data(
            session=session,
            network_id=network.code,
            bucket_size=bucket_size,
            start_date=period_start,
            end_date=period_end,
            fueltech_group=fueltech_group,
        )

        await persist_milestones(
            session=session,
            metrics=[MilestoneMetric.power, MilestoneMetric.emissions, MilestoneMetric.energy],
            aggregates=[MilestoneAggregate.high, MilestoneAggregate.low],
            bucket_size=bucket_size,
            aggregated_data=aggregated_data,
        )

        await session.commit()
