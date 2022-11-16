"""
This worker process updates facility status based on seen generation data

will run once a day from scheduler
"""

import logging

from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility

logger = logging.getLogger("opennem.workers.facility_status")


class OpennemFacilityStatusException(Exception):
    """Exception raised in this module"""

    pass


def update_opennem_facility_status() -> None:
    """Runs a query that will find all comissioning facilities that have
    generation data and updates their status to operating, otherwise they're
    committed
    """

    logger.info("Updating facility status")

    with SessionLocal() as sess:
        # find all facilities that are commissioning
        # and have generation data
        # and update their status to operating
        # otherwise they're committed
        q = (
            sess.query(Facility)
            .filter(Facility.status_id == "commissioning")
            .filter(Facility.data_last_seen.any())
            .update({"status_id": "operating"}, synchronize_session=False)
        )

        logger.info(f"Updated {q} facilities to operating")

        # find all facilities that are commissioning
        # and have no generation data
        # and update their status to committed
        q = (
            sess.query(Facility)
            .filter(Facility.status_id == "commissioning")
            .filter(~Facility.data_last_seen)
            .update({"status_id": "committed"}, synchronize_session=False)
        )

        logger.info(f"Updated {q} facilities to committed")

        sess.commit()

    logger.info("Finished updating facility status")


if __name__ == "__main__":
    update_opennem_facility_status()
