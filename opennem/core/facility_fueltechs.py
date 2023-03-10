import logging

from sqlalchemy.orm import sessionmaker

from opennem.core.loader import load_data_json
from opennem.db import db_connect
from opennem.db.models.opennem import Facility

logger = logging.getLogger(__name__)


def load_facility_fueltech_map() -> None:
    """
    Only do this for DUIDs that don't have a fueltech


    """

    engine = db_connect()
    session = sessionmaker(bind=engine)
    s = session()

    facility_fueltech_map = load_data_json("facility_fueltech_map.json")

    update_count = 0

    for facility_duid, facility_fueltech in facility_fueltech_map.items():
        facilities = s.query(Facility).filter(Facility.network_code == facility_duid).all()

        for f in facilities:
            if f.fueltech_id:
                logger.debug(f"Skipping {f.code} because it already has a fueltech of {f.fueltech_id}")
                continue

            f.fueltech_id = facility_fueltech
            s.add(f)
            update_count += 1

    s.commit()
    logger.info(f"Updated {update_count} fueltechs for facilities")


if __name__ == "__main__":
    load_facility_fueltech_map()
