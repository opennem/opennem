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

from opennem.api import StationSubmission
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


def get_stations(
    name: str = None, limit: Optional[int] = None, page: int = 1
) -> List[Station]:
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
    )

    if name:
        stations = stations.filter(Station.name.like("%{}%".format(name)))

    stations = stations.order_by(
        Facility.network_region,
        Station.name,
        Facility.network_code,
        Facility.code,
    )

    stations = stations.all()

    logger.info("Got {} stations".format(len(stations)))

    return stations


def get_station(station_id: str) -> Station:
    """
        Returns a single station by id

    """
    s = session()

    station = s.query(Station).get(station_id)

    return station


def create_station(station: StationSubmission) -> bool:
    """
        Create a station

    """
    s = session()

    station_record = Station(name=station.name, network_id=station.network_id)

    s.add(station_record)
    s.commit()

    return station_record


if __name__ == "__main__":
    get_stations()
