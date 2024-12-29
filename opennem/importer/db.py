"""Database import and init methods"""

import logging

from opennem.core.stats.store import init_stats
from opennem.db.load_fixtures import load_fixtures
from opennem.importer.rooftop import rooftop_facilities
from opennem.workers.facility_data_seen import update_facility_seen_range

logger = logging.getLogger(__name__)


async def import_all_facilities() -> None:
    await rooftop_facilities()
    logger.info("Rooftop stations initialized")


async def init() -> None:
    """
    These are all the init steps required after a db has been initialized
    """
    await load_fixtures()
    logger.info("Fixtures loaded")

    await import_all_facilities()

    init_stats()
    logger.info("Stats data initialized")

    await update_facility_seen_range()
    logger.info("Ran seen range")
