"""
Methods for current Record Rector state

"""

import asyncio
import logging

from sqlalchemy import text

from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit_by_value
from opennem.db import SessionLocal
from opennem.recordreactor.schema import MilestoneRecordSchema

logger = logging.getLogger("opennem.recordreactor.state")

_CURRENT_MILESTONE_STATE: dict[str, MilestoneRecordSchema] | None = None


async def get_current_milestone_state_from_database() -> dict[str, MilestoneRecordSchema]:
    """
    Gets the most recent milestone for each record_id and returns them in a dict keyed by record_id

    Returns:
        dict[str, MilestoneRecord]: A dictionary of milestone records keyed by record_id

    """
    result_dict: dict[str, MilestoneRecordSchema] = {}

    async with SessionLocal() as session:
        query = text("""
            WITH ranked_records AS (
                SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY record_id ORDER BY "interval" DESC) AS rn
                FROM milestones
            )
            SELECT
                record_id,
                "interval",
                instance_id,
                aggregate,
                metric,
                period,
                significance,
                value,
                value_unit,
                network_id,
                network_region,
                fueltech_id,
                fueltech_group_id,
                description,
                previous_instance_id
            FROM ranked_records
            WHERE rn = 1
            ORDER BY record_id, "interval" DESC
        """)

        result = await session.execute(query)

        for row in result.fetchall():
            result_dict[row[0]] = MilestoneRecordSchema(
                record_id=row[0],
                interval=row[1],
                instance_id=row[2],
                aggregate=row[3],
                metric=row[4],
                period=row[5],
                significance=row[6],
                value=row[7],
                value_unit=get_unit_by_value(row[8]),
                network=network_from_network_code(row[9]),
                network_region=row[10],
                fueltech_id=row[11],
                fueltech_group_id=row[12],
                description=row[13],
            )

    return result_dict


async def get_current_milestone_state() -> dict[str, MilestoneRecordSchema]:
    """
    Gets the current milestone mapping

    Returns:
        dict[str, MilestoneRecord]: A dictionary of milestone records keyed by record_id

    """
    global _CURRENT_MILESTONE_STATE

    if not _CURRENT_MILESTONE_STATE:
        _CURRENT_MILESTONE_STATE = await get_current_milestone_state_from_database()

    return _CURRENT_MILESTONE_STATE


async def refresh_current_milestone_state() -> dict[str, MilestoneRecordSchema]:
    """
    Refreshes the current milestone mapping

    Returns:
        dict[str, MilestoneRecord]: A dictionary of milestone records keyed by record_id
    """
    global _CURRENT_MILESTONE_STATE
    _CURRENT_MILESTONE_STATE = None

    _CURRENT_MILESTONE_STATE = await get_current_milestone_state()

    return _CURRENT_MILESTONE_STATE


if __name__ == "__main__":
    import asyncio

    res = asyncio.run(get_current_milestone_state_from_database())

    for record in res.values():
        print(record)
