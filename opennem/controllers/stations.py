import decimal
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from pprint import pprint
from typing import List, Optional

from geojson import Feature, FeatureCollection, Point, dumps
from sqlalchemy import func

from opennem.db.models.opennem import (
    Facility,
    FacilityStatus,
    FuelTech,
    Network,
    Station,
    metadata,
)
from opennem.schema.opennem import StationSubmission

logger = logging.getLogger(__name__)


def get_stations(
    session, name: str = None, limit: Optional[int] = None, page: int = 1
) -> List[Station]:
    """
        API controller that gets all stations sorted and joined

    """

    stations = (
        session.query(Station)
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


def get_station(session, station_id: str) -> Station:
    """
        Returns a single station by id

    """
    station = session.query(Station).get(station_id)

    return station


def create_station(session, station: StationSubmission) -> Station:
    """
        Create a station

    """
    station_record = Station(name=station.name, network_id=station.network_id)

    session.add(station_record)
    session.commit()

    return station_record
