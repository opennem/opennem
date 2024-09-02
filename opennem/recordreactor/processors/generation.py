"""
RecordReactor generation methods
"""

import logging
from datetime import datetime

from opennem.core.fueltech_group import get_fueltech_group
from opennem.core.units import get_unit
from opennem.queries.energy import get_fueltech_generated_energy_emissions, get_fueltech_interval_energy_emissions
from opennem.recordreactor.buckets import get_bucket_interval
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneMetric,
    MilestonePeriod,
    MilestoneRecordSchema,
)
from opennem.recordreactor.utils import get_bucket_query
from opennem.schema.network import NetworkSchema, NetworkWEM, NetworkWEMDE

logger = logging.getLogger("opennem.recordreactor.controllers.generation")


async def aggregate_generation_and_emissions_data(
    network: NetworkSchema,
    bucket_size: MilestonePeriod,
    date_start: datetime,
    date_end: datetime,
    region_group: bool = True,
) -> list[MilestoneRecordSchema]:
    # logger.info(f"Aggregating generation & emissions data for {network.code} bucket size {bucket_size} for {date_start}")

    query_method = get_fueltech_generated_energy_emissions
    bucket_interval = get_bucket_query(bucket_size, field_name="fs.trading_day")

    if bucket_size == MilestonePeriod.interval:
        bucket_interval = get_bucket_interval(bucket_size, interval_size=network.interval_size)
        query_method = get_fueltech_interval_energy_emissions

    results = await query_method(
        network=network, interval=bucket_interval, date_start=date_start, date_end=date_end, region_group=region_group
    )

    milestone_records: list[MilestoneRecordSchema] = []

    for row in results:
        milestone_records.append(
            MilestoneRecordSchema(
                interval=date_start,
                aggregate=MilestoneAggregate.low,
                metric=MilestoneMetric.power,
                period=bucket_size,
                unit=get_unit("power_mega"),
                network=network,
                network_region=row.network_region if region_group else None,
                fueltech=get_fueltech_group(row.fueltech_id),
                value=row.fueltech_generated,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=date_start,
                aggregate=MilestoneAggregate.high,
                metric=MilestoneMetric.power,
                period=bucket_size,
                unit=get_unit("power_mega"),
                network=network,
                network_region=row.network_region if region_group else None,
                fueltech=get_fueltech_group(row.fueltech_id),
                value=row.fueltech_generated,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=date_start,
                aggregate=MilestoneAggregate.low,
                metric=MilestoneMetric.energy,
                period=bucket_size,
                unit=get_unit("energy_mega"),
                network=network,
                network_region=row.network_region if region_group else None,
                fueltech=get_fueltech_group(row.fueltech_id),
                value=row.fueltech_energy,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=date_start,
                aggregate=MilestoneAggregate.high,
                metric=MilestoneMetric.energy,
                period=bucket_size,
                unit=get_unit("energy_mega"),
                network=network,
                network_region=row.network_region if region_group else None,
                fueltech=get_fueltech_group(row.fueltech_id),
                value=row.fueltech_energy,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=date_start,
                aggregate=MilestoneAggregate.low,
                metric=MilestoneMetric.emissions,
                period=bucket_size,
                unit=get_unit("emissions"),
                network=network,
                network_region=row.network_region if region_group else None,
                fueltech=get_fueltech_group(row.fueltech_id),
                value=row.fueltech_emissions,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=date_start,
                aggregate=MilestoneAggregate.high,
                metric=MilestoneMetric.emissions,
                period=bucket_size,
                unit=get_unit("emissions"),
                network=network,
                network_region=row.network_region if region_group else None,
                fueltech=get_fueltech_group(row.fueltech_id),
                value=row.fueltech_emissions,
            )
        )

    return milestone_records


async def run_generation_energy_emissions_milestones(
    network: NetworkSchema, bucket_size: MilestonePeriod, period_start: datetime, period_end: datetime
):
    if bucket_size == MilestonePeriod.interval:
        return

    milestone_data = await aggregate_generation_and_emissions_data(
        network=network,
        bucket_size=bucket_size,
        date_start=period_start,
        date_end=period_end,
        region_group=False,
    )

    await persist_milestones(
        milestones=milestone_data,
    )

    # don't region group for WEM/WEMDE as they are not region specific
    if network in [NetworkWEM, NetworkWEMDE]:
        return

    milestone_data = await aggregate_generation_and_emissions_data(
        network=network,
        bucket_size=bucket_size,
        date_start=period_start,
        date_end=period_end,
        region_group=True,
    )

    await persist_milestones(
        milestones=milestone_data,
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
