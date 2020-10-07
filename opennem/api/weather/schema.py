from datetime import date, datetime
from typing import List, Optional

from opennem.api.schema import ApiBase


class WeatherObservation(ApiBase):
    observation_time: datetime
    station_id: int

    temp_apparent: float
    temp_air: float
    press_qnh: float
    wind_dir: Optional[str]
    wind_spd: float


class WeatherStation(ApiBase):
    code: str
    state: str
    name: str
    registered: date
    lat: float
    lng: float

    observations: Optional[List[WeatherObservation]]
