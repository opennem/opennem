from datetime import date, datetime
from typing import List, Optional

from opennem.api.schema import ApiBase


class WeatherObservation(ApiBase):
    observation_time: datetime
    station_id: int

    temp_apparent: float
    temp_air: float
    press_qnh: Optional[float]
    wind_dir: Optional[str]
    wind_spd: Optional[float]
    wind_gust: Optional[float]
    humidity: Optional[float]
    cloud: Optional[str]
    cloud_type: Optional[str]


class WeatherStation(ApiBase):
    code: str
    state: str
    name_alias: str
    registered: Optional[date]
    website_url: str
    altitude: int
    lat: float
    lng: float

    observations: Optional[List[WeatherObservation]]
