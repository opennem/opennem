"""
RecordReactor power methods
"""

import asyncio
import logging
from datetime import datetime
from itertools import product

from sqlalchemy import text

from opennem.core.fueltech_group import get_fueltech_group
from opennem.core.units import get_unit
from opennem.db import get_read_session
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneMetric,
    MilestonePeriod,
    MilestoneRecordSchema,
)
from opennem.schema.network import NetworkSchema, NetworkWEM, NetworkWEMDE

logger = logging.getLogger("opennem.recordreactor.controllers.power")


async def milestone_aggregate_power_data(
    network: NetworkSchema,
    bucket_size: MilestonePeriod,
    date_start: datetime,
    group_by_region: bool = False,
    group_by_fueltech: bool = False,
) -> list[MilestoneRecordSchema]:
    if network in [NetworkWEM, NetworkWEMDE]:
        return []

    if not network.subnetworks:
        raise ValueError("Network must have sub networks")

    interval_size = network.interval_size

    query = text(f"""
        SELECT
            '{network.code.upper()}' AS network_id,
            CASE WHEN {group_by_region} THEN f.network_region ELSE 'all' end as network_region,
            CASE WHEN {group_by_fueltech}  THEN ftg.code         ELSE 'all' end as fueltech_group,
            time_bucket('{interval_size} minutes', fs.interval) AS interval,
            COALESCE(sum(generated), 0) AS generation
        FROM facility_scada fs
        JOIN facility f ON f.code = fs.facility_code
        JOIN fueltech ft ON ft.code = f.fueltech_id
        JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
        WHERE
            fs.interval = '{date_start}' AND
            fs.network_id IN ('{network.code.upper()}', {', '.join([f"'{i.code.upper()}'" for i in network.subnetworks])}) AND
            fs.is_forecast is False
        GROUP BY
            1, 2, 3, 4
        ORDER BY
            1, 2, 3
    """)

    async with get_read_session() as session:
        result = await session.execute(
            query,
        )

        results = result.fetchall()

    milestone_records: list[MilestoneRecordSchema] = []

    for row in results:
        for agg in [MilestoneAggregate.high, MilestoneAggregate.low]:
            milestone_records.append(
                MilestoneRecordSchema(
                    interval=row.interval,
                    aggregate=agg,
                    metric=MilestoneMetric.power,
                    period=bucket_size,
                    unit=get_unit("power_mega"),
                    network=network,
                    network_region=row.network_region if group_by_region else None,
                    fueltech=get_fueltech_group(row.fueltech_group) if group_by_fueltech else None,
                    value=row.generation,
                )
            )

    return milestone_records


async def run_power_milestones(
    network: NetworkSchema, bucket_size: MilestonePeriod, period_start: datetime, period_end: datetime
):
    if bucket_size != MilestonePeriod.interval:
        return

    async def _run_and_persist(region_group: bool, fueltech_group: bool):
        milestone_data = await milestone_aggregate_power_data(
            network=network,
            bucket_size=bucket_size,
            date_start=period_start,
            group_by_region=region_group,
            group_by_fueltech=fueltech_group,
        )

        await persist_milestones(
            milestones=milestone_data,
        )

    tasks = []
    for region_group, fueltech_group in product([True, False], [True, False]):
        tasks.append(_run_and_persist(region_group=region_group, fueltech_group=fueltech_group))

    if tasks:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta

    from opennem.schema.network import NetworkNEM

    logging.basicConfig(level=logging.INFO)

    # 2018-02-26 23:50:00+10:00
    start_interval = datetime.fromisoformat("2024-01-01 00:00:00")
    end_interval = start_interval + timedelta(minutes=5)
    # end_interval = datetime.fromisoformat("2024-01-01 00:05:00")
    res = asyncio.run(
        milestone_aggregate_power_data(
            network=NetworkNEM,
            bucket_size=MilestonePeriod.interval,
            date_start=start_interval,
            group_by_region=True,
            group_by_fueltech=True,
        )
    )
    for r in res:
        print(r)
