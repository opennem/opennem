from opennem.db import SessionLocal
from opennem.db.models.opennem import BomStation


def get_stations_priority():
    session = SessionLocal()

    stations = session.query(BomStation).filter(BomStation.priority < 2).all()

    return stations


def get_stations():
    session = SessionLocal()

    stations = session.query(BomStation).filter(BomStation.priority >= 2).all()

    return stations
