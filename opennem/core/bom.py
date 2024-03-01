"""OpenNEM Core BoM Station Utilities

Get a list of stations from the local database
"""

from datetime import date, datetime
from random import shuffle

from opennem.db import SessionLocal
from opennem.db.models.opennem import BomStation
from opennem.schema.bom import BomStationSchema


def get_stations_priority(limit: int | None = None) -> list[BomStationSchema]:
    """This gets all the capital stations which are required for the linked regions"""
    with SessionLocal() as session:
        stations = session.query(BomStation).filter(BomStation.priority < 2).all()

        all_models = [BomStationSchema.from_orm(i) for i in stations]
        return_models = []

        if limit:
            if limit > len(all_models):
                return all_models

            # shuffle the list of stations and pick a random number out
            shuffle(all_models)

            return_models = all_models[:limit]
        else:
            shuffle(all_models)
            return_models = all_models

    return return_models


def get_stations() -> list[BomStationSchema]:
    """Get all weather stations

    @NOTE This is a bit redundant
    """
    with SessionLocal() as session:
        stations = session.query(BomStation).filter(BomStation.priority >= 2).all()

        all_models = [BomStationSchema.from_orm(i) for i in stations]

    return all_models


def get_archive_page_for_station_code(web_code: str, archive_month: date = datetime.now()) -> str:
    """returns a station archive page for a web code and a month"""
    url_format = "http://www.bom.gov.au/climate/dwo/{datestr}/html/IDCJDW{web_code}.{datestr}.shtml"

    return url_format.format(datestr=archive_month.strftime("%Y%m"), web_code=web_code)
