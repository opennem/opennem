from datetime import date, datetime
from typing import List

from sqlalchemy.sql.operators import from_

from opennem.db import SessionLocal
from opennem.db.models.opennem import BomStation
from opennem.schema.bom import BomStationSchema

BOM_REQUEST_HEADERS = {
    "Host": "www.bom.gov.au",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


def get_stations_priority() -> List[BomStationSchema]:
    """This gets all the capital stations which are required for the linked regions"""
    session = SessionLocal()

    stations = session.query(BomStation).filter(BomStation.priority < 2).all()

    _models = [BomStationSchema.from_orm(i) for i in stations]

    return _models


def get_stations() -> List[BomStation]:
    """Get all weather stations"""
    session = SessionLocal()

    stations = session.query(BomStation).filter(BomStation.priority >= 2).all()

    return stations


def get_archive_page_for_station_code(web_code: str, archive_month: date = datetime.now()) -> str:
    """returns a station archive page for a web code and a month"""
    url_format = (
        "http://www.bom.gov.au/climate/dwo/{datestr}/html/IDCJDW{web_code}.{datestr}.shtml"
    )

    return url_format.format(datestr=archive_month.strftime("%Y%m"), web_code=web_code)
