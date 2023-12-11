"""
OpenNEM Milestone Records Reactor Database Persistence


"""

import logging

from opennem.db import get_database_engine
from opennem.db.models.opennem import Milestones

logger = logging.getLogger("opennem.milestones.reactor")


def persist_milestones(milestons: list[Milestones]) -> int:
    """Persist milestones to database with upsert query"""

    engine = get_database_engine()

    if not engine:
        raise Exception("No engine")

    conn = engine.connect()

    for milestone in milestons:
        logger.info(f"Persisting milestone {milestone.network_id} {milestone.facility_code} {milestone.interval}")

        conn.execute(
            """
            insert into milestones (
                network_id,
                facility_code,
                interval,
                milestone_type,
                milestone_value
            ) values (
                :network_id,
                :facility_code,
                :interval,
                :milestone_type,
                :milestone_value
            ) on conflict (network_id, facility_code, interval, milestone_type) do update set
                milestone_value = :milestone_value
            """,
            **milestone.dict(),
        )

    conn.close()

    return len(milestons)
