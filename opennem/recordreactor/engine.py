"""
RecordReactor engine
"""

import logging
from datetime import datetime, timedelta

from opennem import settings
from opennem.recordreactor.buckets import BUCKET_SIZES, get_period_start_end, is_end_of_period
from opennem.recordreactor.controllers.demand import run_price_demand_milestone_for_interval
from opennem.recordreactor.controllers.generation import run_generation_energy_emissions_milestones
from opennem.recordreactor.schema import MilestoneMetric
from opennem.schema.network import NetworkNEM, NetworkWEM, NetworkWEMDE
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.recordreactor.engine")


async def run_milestone_engine(
    start_interval: datetime, end_interval: datetime | None = None, milestone_metrics: list[MilestoneMetric] | None = None
):
    if not milestone_metrics:
        milestone_metrics = [
            MilestoneMetric.demand,
            MilestoneMetric.price,
            MilestoneMetric.power,
            MilestoneMetric.energy,
            MilestoneMetric.emissions,
        ]

    num_tasks = 14

    for network in [NetworkNEM, NetworkWEM, NetworkWEMDE]:
        if not network.interval_size:
            logger.info(f"Skipping {network.code} as it has no interval size")
            continue

        if not network.data_first_seen:
            logger.info(f"Skipping {network.code} as it has no data first seen")
            continue

        logger.info(f"Processing price and demand milestone data network {network.code}")

        if not end_interval:
            end_interval = get_last_completed_interval_for_network(network)
            logger.info(f"Set end interval for {network.code} to {end_interval}")

        current_interval = start_interval
        tasks = []

        while current_interval <= end_interval:
            # Process each bucket size for this interval

            if network.data_last_seen and current_interval > network.data_last_seen.replace(tzinfo=None):
                logger.info(f"Breaking at {current_interval} as it is after the last data seen for {network.code}")
                break

            if current_interval < network.data_first_seen.replace(tzinfo=None):
                logger.info(f"Skipping {current_interval} as it is before the first data seen for {network.code}")
                current_interval += timedelta(minutes=network.interval_size)
                continue

            for bucket_size in BUCKET_SIZES:
                if is_end_of_period(current_interval, bucket_size):
                    period_start, period_end = get_period_start_end(current_interval, bucket_size)

                    if settings.dry_run:
                        continue

                    if MilestoneMetric.demand in milestone_metrics or MilestoneMetric.price in milestone_metrics:
                        task = run_price_demand_milestone_for_interval(
                            network=network,
                            bucket_size=bucket_size,
                            period_start=period_start,
                            period_end=period_end,
                        )
                        tasks.append(task)

                    if (
                        MilestoneMetric.power in milestone_metrics
                        or MilestoneMetric.energy in milestone_metrics
                        or MilestoneMetric.emissions in milestone_metrics
                    ):
                        task = run_generation_energy_emissions_milestones(
                            network=network,
                            bucket_size=bucket_size,
                            period_start=period_start,
                            period_end=period_end,
                        )
                        tasks.append(task)

            # Move to the next interval
            current_interval += timedelta(minutes=network.interval_size)

            if len(tasks) >= num_tasks:  # Adjust this number based system's capabilities
                await asyncio.gather(*tasks)
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)


# Usage
if __name__ == "__main__":
    import asyncio

    # 2018-02-26 23:50:00+10:00
    start_interval = datetime.fromisoformat("2024-01-01 00:00:00")
    end_interval = datetime.fromisoformat("2024-08-01 00:00:00")
    asyncio.run(run_milestone_engine(start_interval=start_interval, end_interval=end_interval))
