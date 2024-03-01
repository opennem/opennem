"""Database import and init methods"""

import logging

from opennem.core.stats.store import init_stats
from opennem.db.load_fixtures import load_fixtures
from opennem.importer.facilities import import_facilities
from opennem.importer.interconnectors import import_nem_interconnects
from opennem.importer.rooftop import rooftop_facilities
from opennem.workers.facility_data_ranges import update_facility_seen_range

logger = logging.getLogger(__name__)


def import_all_facilities() -> None:
    import_facilities()
    logger.info("OpenNEM stations imported")

    rooftop_facilities()
    logger.info("Rooftop stations initialized")

    import_nem_interconnects()
    logger.info("Interconnectors initialized")


def init() -> None:
    """
    These are all the init steps required after a db has been initialized
    """
    load_fixtures()
    logger.info("Fixtures loaded")

    import_all_facilities()

    init_stats()
    logger.info("Stats data initialized")

    update_facility_seen_range()
    logger.info("Ran seen range")
