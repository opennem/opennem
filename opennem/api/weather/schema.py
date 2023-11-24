from datetime import date, datetime

from opennem.api.schema import ApiBase


class WeatherObservation(ApiBase):
    observation_time: datetime
    station_id: int

    temp_apparent: float
    temp_air: float
    press_qnh: float | None = None
    wind_dir: str | None = None
    wind_spd: float | None = None
    wind_gust: float | None = None
    humidity: float | None = None
    cloud: str | None = None
    cloud_type: str | None = None


class WeatherStation(ApiBase):
    code: str
    state: str
    name_alias: str
    registered: date | None = None
    website_url: str
    altitude: int
    lat: float
    lng: float

    observations: list[WeatherObservation] | None = None
