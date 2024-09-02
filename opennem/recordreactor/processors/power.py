"""
RecordReactor power methods
"""

import logging
from datetime import datetime

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
    date_end: datetime,
    group_by_region: bool = False,
    group_by_fueltech: bool = False,
) -> list[MilestoneRecordSchema]:
    if not network.subnetworks:
        raise ValueError("Network must have sub networks")

    interval_size = network.interval_size

    query = text(f"""
        WITH generation_totals AS (
            SELECT
                :network_id AS network_id,
                f.network_region,
                ftg.code AS fueltech_group,
                time_bucket('{interval_size} minutes', fs.interval) AS bucketed_time,
                SUM(generated) AS total_generation
            FROM facility_scada fs
            JOIN facility f ON f.code = fs.facility_code
            JOIN fueltech ft ON ft.code = f.fueltech_id
            JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
            WHERE
                fs.interval >= :start_date AND
                fs.interval < :end_date AND
                fs.network_id = ANY(:network_ids)
            GROUP BY 1, f.network_region, ftg.code, bucketed_time
        ),
        ranked_generation AS (
            SELECT
                network_id,
                network_region,
                fueltech_group,
                bucketed_time,
                total_generation,
                ROW_NUMBER() OVER (
                    PARTITION BY
                        network_id,
                        CASE WHEN :group_by_region THEN network_region ELSE NULL END,
                        CASE WHEN :group_by_fueltech THEN fueltech_group ELSE NULL END
                    ORDER BY total_generation DESC
                ) AS peak_rank,
                ROW_NUMBER() OVER (
                    PARTITION BY
                        network_id,
                        CASE WHEN :group_by_region THEN network_region ELSE NULL END,
                        CASE WHEN :group_by_fueltech THEN fueltech_group ELSE NULL END
                    ORDER BY total_generation ASC
                ) AS min_rank
            FROM generation_totals
        )
        SELECT
            network_id,
            CASE WHEN :group_by_region THEN network_region ELSE 'All Regions' END AS region,
            CASE WHEN :group_by_fueltech THEN fueltech_group ELSE 'All Fueltechs' END AS fueltech_group,
            MAX(CASE WHEN peak_rank = 1 THEN bucketed_time END) AS peak_interval,
            MAX(CASE WHEN peak_rank = 1 THEN total_generation END) AS peak_generation,
            MAX(CASE WHEN min_rank = 1 THEN bucketed_time END) AS min_interval,
            MAX(CASE WHEN min_rank = 1 THEN total_generation END) AS min_generation
        FROM ranked_generation
        GROUP BY
            network_id,
            CASE WHEN :group_by_region THEN network_region ELSE 'All Regions' END,
            CASE WHEN :group_by_fueltech THEN fueltech_group ELSE 'All Fueltechs' END
        ORDER BY network_id, region, fueltech_group;
    """)

    params = {
        "network_id": network.code,
        "network_ids": [i.code for i in network.subnetworks],
        "start_date": date_start,
        "end_date": date_end,
        "group_by_region": group_by_region,
        "group_by_fueltech": group_by_fueltech,
    }

    async with get_read_session() as session:
        result = await session.execute(
            query,
            params,
        )

        results = result.fetchall()

    milestone_records: list[MilestoneRecordSchema] = []

    for row in results:
        milestone_records.append(
            MilestoneRecordSchema(
                interval=row.peak_interval,
                aggregate=MilestoneAggregate.high,
                metric=MilestoneMetric.power,
                period=bucket_size,
                unit=get_unit("power_mega"),
                network=network,
                network_region=row.region if group_by_region else None,
                fueltech=get_fueltech_group(row.fueltech_group) if group_by_fueltech else None,
                value=row.peak_generation,
            )
        )

        milestone_records.append(
            MilestoneRecordSchema(
                interval=row.min_interval,
                aggregate=MilestoneAggregate.low,
                metric=MilestoneMetric.power,
                period=bucket_size,
                unit=get_unit("power_mega"),
                network=network,
                network_region=row.region if group_by_region else None,
                fueltech=get_fueltech_group(row.fueltech_group) if group_by_fueltech else None,
                value=row.min_generation,
            )
        )

    return milestone_records


async def run_power_milestones(
    network: NetworkSchema, bucket_size: MilestonePeriod, period_start: datetime, period_end: datetime
):
    milestone_data = await milestone_aggregate_power_data(
        network=network,
        bucket_size=bucket_size,
        date_start=period_start,
        date_end=period_end,
        group_by_region=False,
    )

    await persist_milestones(
        milestones=milestone_data,
    )

    # don't region group for WEM/WEMDE as they are not region specific
    if network in [NetworkWEM, NetworkWEMDE]:
        return

    milestone_data = await milestone_aggregate_power_data(
        network=network,
        bucket_size=bucket_size,
        date_start=period_start,
        date_end=period_end,
        group_by_region=True,
    )

    await persist_milestones(
        milestones=milestone_data,
    )


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta

    from opennem.schema.network import NetworkNEM

    logging.basicConfig(level=logging.INFO)

    # 2018-02-26 23:50:00+10:00
    start_interval = datetime.fromisoformat("2024-01-01 00:00:00")
    end_interval = start_interval + timedelta(days=1)
    end_interval = datetime.fromisoformat("2024-02-01 00:00:00")
    res = asyncio.run(
        milestone_aggregate_power_data(
            network=NetworkNEM,
            bucket_size=MilestonePeriod.month,
            date_start=start_interval,
            date_end=end_interval,
            group_by_region=False,
            group_by_fueltech=True,
        )
    )
    for r in res:
        print(r)
