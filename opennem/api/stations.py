import decimal
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from pprint import pprint
from typing import List

from geojson import Feature, FeatureCollection, Point, dumps
from smart_open import open
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


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_stations() -> List[Station]:
    s = session()

    logger.info("Running query")

    stations = (
        s.query(Station)
        .join(Facility)
        .join(FuelTech)
        # , Network, FacilityStatus)
        .filter(Facility.fueltech != None)
        .order_by(Station.id)
        .all()
    )

    logger.info("Got {} stations".format(len(stations)))

    # for station in stations:
    # print(station.id, station.code, station.name)

    return stations


if __name__ == "__main__":
    get_stations()
