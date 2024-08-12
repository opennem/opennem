"""
RecordReactor generation methods
"""

import logging
from datetime import datetime

from opennem.queries.energy import get_fueltech_generated_energy_emissions
from opennem.recordreactor.buckets import get_bucket_interval
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.recordreactor.controllers.generation")


async def aggregate_generation_and_emissions_data(
    network: NetworkSchema,
    bucket_size: str,
    date_start: datetime,
    date_end: datetime,
) -> list[dict]:
    logger.info(f"Aggregating generation & emissions data for {network.code} bucket size {bucket_size} for {date_start}")

    bucket_interval = get_bucket_interval(bucket_size, interval_size=network.interval_size)

    results = await get_fueltech_generated_energy_emissions(
        network=network, interval=bucket_interval, date_start=date_start, date_end=date_end
    )

    return [
        {
            "bucket": row.interval,
            "network_id": row.network_id if row.network_id not in ["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"] else "NEM",
            "network_region": row.network_region,
            "fueltech_id": row.fueltech_id,
            "power_low": row.fueltech_generated,
            "power_high": row.fueltech_generated,
            "energy_low": row.fueltech_energy,
            "energy_high": row.fueltech_energy,
            "emissions_low": row.fueltech_emissions,
            "emissions_high": row.fueltech_emissions,
        }
        for row in results
    ]


async def run_generation_energy_emissions_milestones(
    network: NetworkSchema, bucket_size: str, period_start: datetime, period_end: datetime
):
    aggregated_data = await aggregate_generation_and_emissions_data(
        network=network,
        bucket_size=bucket_size,
        date_start=period_start,
        date_end=period_end,
    )

    await persist_milestones(
        metrics=[MilestoneMetric.power, MilestoneMetric.emissions, MilestoneMetric.energy],
        aggregates=[MilestoneAggregate.high, MilestoneAggregate.low],
        bucket_size=bucket_size,
        aggregated_data=aggregated_data,
    )


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta

    from opennem.schema.network import NetworkNEM

    # 2018-02-26 23:50:00+10:00
    start_interval = datetime.fromisoformat("2024-08-01 00:00:00")
    end_interval = start_interval + timedelta(days=1)
    res = asyncio.run(
        aggregate_generation_and_emissions_data(
            network=NetworkNEM, bucket_size="1 day", date_start=start_interval, date_end=end_interval
        )
    )
    for r in res:
        print(r)
