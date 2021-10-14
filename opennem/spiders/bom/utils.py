from datetime import date, datetime
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


def get_archive_page_for_station_code(web_code: str, archive_month: date = datetime.now()) -> str:
    """ returns a station archive page for a web code and a month"""
    url_format = "http://www.bom.gov.au/climate/dwo/{datestr}/html/IDCJDW{web_code}.{datestr}.shtml"

    return url_format.format(datestr=archive_month.strftime("%Y%m"), web_code=web_code)


