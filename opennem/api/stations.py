import decimal
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from pprint import pprint
from typing import List

from geojson import Feature, FeatureCollection, Point, dumps
from smart_open import open
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import (
    Facility,
    FacilityStatus,
    FuelTech,
    Network,
    Station,
    metadata,
)

engine = db_connect()
session = sessionmaker(bind=engine)

logger = logging.getLogger(__name__)


def get_stations() -> List[Station]:
    """
        API controller that gets all stations sorted and joined

    """
    s = session()

    stations = (
        s.query(Station)
        .join(Facility)
        .join(Facility.fueltech)
        .filter(Facility.fueltech_id.isnot(None))
        .filter(Facility.status_id.isnot(None))
        .order_by(
            Facility.network_region,
            Station.name,
            Station.id,
            Facility.unit_number,
            Facility.code,
        )
        .all()
    )

    logger.info("Got {} stations".format(len(stations)))

    return stations


if __name__ == "__main__":
    get_stations()
