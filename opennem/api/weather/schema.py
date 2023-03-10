from datetime import date, datetime

from opennem.api.schema import ApiBase


class WeatherObservation(ApiBase):
    observation_time: datetime
    station_id: int

    temp_apparent: float
    temp_air: float
    press_qnh: float | None
    wind_dir: str | None
    wind_spd: float | None
    wind_gust: float | None
    humidity: float | None
    cloud: str | None
    cloud_type: str | None


class WeatherStation(ApiBase):
    code: str
    state: str
    name_alias: str
    registered: date | None
    website_url: str
    altitude: int
    lat: float
    lng: float

    observations: list[WeatherObservation] | None
