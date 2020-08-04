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
    s = session()

    stations = []

    query = (
        s.query(Station, func.st_x(Station.geom), func.st_y(Station.geom))
        .join(Facility)
        .join(FuelTech)
        # , Network, FacilityStatus)
        .filter(Facility.fueltech != None)
        .filter(Facility.status != None)
        .order_by(
            # Station.network_region,
            # Station.id,
            Facility.network_region,
            Station.name,
            Station.id,
            Facility.unit_number,
            Facility.code,
        )
        .all()
    )

    logger.info("Got {} stations".format(len(stations)))

    # Bind lat long using postgis functions
    # note this isn't x-db compatible atm
    for i in query:
        station, lat, lng = i
        station.lat = lat
        station.lng = lng
        stations.append(station)

    return stations


if __name__ == "__main__":
    get_stations()
