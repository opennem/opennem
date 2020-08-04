import json
import logging
import os

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.core import load_data_json
from opennem.db import db_connect
from opennem.db.models.opennem import Facility

logger = logging.getLogger(__name__)


def load_facility_fueltech_map():
    """
        Only do this for DUIDs that don't have a fueltech


    """

    engine = db_connect()
    session = sessionmaker(bind=engine)
    s = session()

    facility_fueltech_map = load_data_json("facility_fueltech_map.json")

    update_count = 0

    for facility_duid, facility_fueltech in facility_fueltech_map.items():

        facilities = (
            s.query(Facility)
            .filter(Facility.network_code == facility_duid)
            .all()
        )

        for f in facilities:
            if f.fueltech_id:
                logger.debug(
                    "Skipping {} because it already has a fueltech of {}".format(
                        f.code, f.fueltech_id
                    )
                )
                continue

            f.fueltech_id = facility_fueltech
            s.add(f)
            update_count += 1

    s.commit()
    logger.info("Updated {} fueltechs for facilities".format(update_count))


if __name__ == "__main__":
    load_facility_fueltech_map()
