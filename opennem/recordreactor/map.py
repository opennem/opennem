"""
Defines the milestone map and MilestoneSchemas
"""

import logging
from itertools import product

from opennem.recordreactor.schema import (
    MILESTONE_SUPPORTED_NETWORKS,
    MilestoneAggregate,
    MilestoneMetric,
    MilestonePeriod,
    MilestoneSchema,
)
from opennem.recordreactor.utils import get_record_unit_by_metric

logger = logging.getLogger("opennem.recordreactor.map")

_MILESTONE_MAP = {}


async def generate_milestone_map() -> dict[str, MilestoneSchema]:
    """
    Generate a list of milestone schemas for all supported mileston types

    Returns:
        list[MilestoneSchema]: A list of milestone schemas
    """
    milestone_records = {}

    for network, aggregate, metric, period in product(
        MILESTONE_SUPPORTED_NETWORKS, MilestoneAggregate, MilestoneMetric, MilestonePeriod
    ):
        if not network.regions:
            continue

        for network_region in network.regions:
            milestone_schema = MilestoneSchema(
                aggregate=aggregate,
                metric=metric,
                period=period,
                unit=get_record_unit_by_metric(metric),
                network_id=network,
                network_region=network_region,
                fueltech_id=None,
                fueltech_group_id=None,
            )

            milestone_records[milestone_schema.record_id] = milestone_schema

    return milestone_records


async def get_milestone_map() -> dict[str, MilestoneSchema]:
    global _MILESTONE_MAP

    if not _MILESTONE_MAP:
        _MILESTONE_MAP = await generate_milestone_map()

    return _MILESTONE_MAP


async def get_milestone_map_by_record_id(record_id: str) -> MilestoneSchema:
    milestone_records = await get_milestone_map()

    if record_id not in milestone_records:
        raise ValueError(f"Invalid record_id: {record_id}")

    return milestone_records[record_id]


if __name__ == "__main__":
    import asyncio

    mmap = asyncio.run(generate_milestone_map())

    for record_id, _ in mmap.items():
        print(record_id)

    print(f"have {len(mmap)} milestones")
