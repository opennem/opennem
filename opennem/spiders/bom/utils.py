from typing import List

from opennem.db import SessionLocal
from opennem.db.models.opennem import BomStation, Station


def get_stations_priority() -> List[Station]:
    """ This gets all the capital stations which are required for the linked regions """
    session = SessionLocal()

    stations = session.query(BomStation).filter(BomStation.priority < 2).all()

    return stations


def get_stations() -> List[Station]:
    """ Get all weather stations """
    session = SessionLocal()

    stations = session.query(BomStation).filter(BomStation.priority >= 2).all()

    return stations
