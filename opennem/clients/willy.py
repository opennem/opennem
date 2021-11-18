#!/usr/bin/env python
import logging
from pprint import pprint
from typing import Any, Dict

from sqlalchemy.dialects.postgresql import insert

from opennem import settings
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BomObservation
from opennem.utils.dates import unix_timestamp_to_aware_datetime
from opennem.utils.http import http

logger = logging.getLogger("opennem.clients.willy")

# Location to bom map
WILLY_MAP = {
    "066214": 4988,  # NSW1 - Observatory Hill
}

WILLY_STATION_URL = (
    "https://api.willyweather.com.au/v2/{api_key}/weather-stations/{station_id}.json"
)
WILLY_LOCATION_URL = (
    "https://api.willyweather.com.au/v2/{api_key}/locations/{location_id}/weather.json"
)
WILLY_SEARCH_URL = "https://api.willyweather.com.au/v2/{api_key}/search.json"
WILLY_SEARCH_CLOSEST_URL = "https://api.willyweather.com.au/v2/{api_key}/search/closest.json"


class WillyClient:
    """Client for Willy Weather API"""

    def __init__(self) -> None:
        if not settings.willyweather_api_key:
            raise Exception("No willy weather API key")

    def _req(self, url: str, params: Dict[str, Any]) -> Dict:
        resp = http.get(url, params=params)

        print(resp.request.body)

        if not resp.ok:
            logger.error("ERROR: {} Response code: {}".format(url, resp.status_code))

        _j = resp.json()

        if "success" in _j and _j["success"] is False:
            raise Exception("{}: {}".format(_j["error"]["code"], _j["error"]["description"]))

        return _j

    def get_station_url(self, station_id: int) -> str:
        return WILLY_STATION_URL.format(
            api_key=settings.willyweather_api_key, station_id=str(station_id)
        )

    def get_location_url(self, location_id: int) -> str:
        return WILLY_LOCATION_URL.format(
            api_key=settings.willyweather_api_key, location_id=location_id
        )

    def get_search_url(self) -> str:
        return WILLY_SEARCH_URL.format(
            api_key=settings.willyweather_api_key,
        )

    def get_search_closest_url(self) -> str:
        return WILLY_SEARCH_CLOSEST_URL.format(
            api_key=settings.willyweather_api_key,
        )

    def search_station(self, query: str, limit: int = 4) -> Dict:
        url = self.get_search_url()

        resp = self._req(url, {"query": query, "limit": limit})

        return resp

    def search_closest(self, id: int) -> Dict:
        url = self.get_search_closest_url()

        resp = self._req(url, {"id": id, "weatherTypes": ["general"], "units": "distance:km"})

        return resp

    def get_station_temp(
        self, station_id: int, days: int = 1, start_date: str = "2021-10-15"
    ) -> Dict:
        url = self.get_station_url(station_id)

        resp = self._req(
            url, {"observationalGraphs": ["temperature"], "days": days, "startDate": start_date}
        )

        return resp

    def get_location_temp(
        self, location_id: int, days: int = 1, start_date: str = "2021-10-15"
    ) -> Dict:
        url = self.get_location_url(location_id)

        resp = self._req(
            url, {"observationalGraphs": ["temperature"], "days": days, "startDate": start_date}
        )

        return resp


def get_station_weather() -> None:
    pass


def update_weather() -> None:
    wc = WillyClient()

    for bom_code, willyid in WILLY_MAP.items():
        r = wc.get_location_temp(willyid, days=3, start_date="2021-10-14")
        data_points = r["observationalGraphs"]["temperature"]["dataConfig"]["series"]["groups"]

        records = []
        pprint(r)

        for pointset in data_points:
            # print(p)
            for p in pointset["points"]:
                r_dict = {
                    "station_id": bom_code,
                    "observation_time": unix_timestamp_to_aware_datetime(
                        p["x"], "Australia/Sydney"
                    ),
                    "temp_air": p["y"],
                }
                print("{} -> {}".format(r_dict["observation_time"], r_dict["temp_air"]))
                records.append(r_dict)

    session = SessionLocal()
    engine = get_database_engine()

    stmt = insert(BomObservation).values(records)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["observation_time", "station_id"],
        set_={
            # "temp_apparent": stmt.excluded.temp_apparent,
            "temp_air": stmt.excluded.temp_air,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error: {}".format(e))
    finally:
        session.close()


if __name__ == "__main__":
    update_weather()
