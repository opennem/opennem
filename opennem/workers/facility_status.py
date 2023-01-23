"""
This worker process updates facility status based on seen generation data

will run once a day from scheduler
"""

import logging

from opennem.db import get_database_engine

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

    engine = get_database_engine()

    with engine.begin() as conn:
        # find all facilities that are commissioning
        # and have generation data
        # and update their status to operating
        # otherwise they're committed

        _query = """
        with operational_facs as (
            select
                f.code,
                f.status_id,
                f.data_last_seen
            from facility f
            where
                f.status_id = 'commissioning'
                and f.data_last_seen is not null
        )
        update facility f set
            status_id = 'operating'
        from operational_facs
            where f.code = operational_facs.code
        """
        conn.execute(_query)

        # find all facilities that are commissioning
        # and have no generation data
        # and update their status to committed
        _query = """
        with operational_facs as (
            select
                f.code,
                f.status_id,
                f.data_last_seen
            from facility f
            where
                f.status_id = 'commissioning'
                and f.data_last_seen is null
        )
        update facility f set
            status_id = 'committed'
        from operational_facs
            where f.code = operational_facs.code

        """

        conn.execute(_query)

    logger.info("Finished updating facility status")


if __name__ == "__main__":
    update_opennem_facility_status()
