"""OpenNEM BoM Client

"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz
import requests
from pydantic import validator

from opennem.schema.core import BaseConfig
from opennem.utils.random_agent import get_random_agent
from opennem.utils.timezone import UTC

logger = logging.getLogger("opennem.clients.bom")

BOM_REQUEST_HEADERS = {
    "Host": "www.bom.gov.au",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


STATE_TO_TIMEZONE = {
    "QLD": "Australia/Brisbane",
    "NSW": "Australia/Sydney",
    "VIC": "Australia/Melbourne",
    "TAS": "Australia/Hobart",
    "SA": "Australia/Adelaide",
    "NT": "Australia/Darwin",
    "WA": "Australia/Perth",
}


def _clean_bom_text_field(field_val: str) -> Optional[str]:
    """Takes the messy BOM string fields and cleans them up"""
    _v = field_val.strip().replace("-", "")

    if len(_v) == 0 or not _v:
        return None

    return _v


class BOMObserationSchema(BaseConfig):
    state: str
    aifstime_utc: str
    observation_time: Optional[datetime]
    apparent_t: float
    air_temp: float
    press_qnh: float
    wind_dir: str
    wind_spd_kmh: Optional[float]
    gust_kmh: Optional[float]
    rel_hum: float
    cloud: Optional[str]
    cloud_type: Optional[str]

    _validate_cloud = validator("cloud", pre=True, allow_reuse=True)(_clean_bom_text_field)
    _validate_cloud_type = validator("cloud_type", pre=True, allow_reuse=True)(
        _clean_bom_text_field
    )

    @validator("observation_time", always=True, pre=True)
    def _validate_observation_time(cls, value: str, values: Dict[str, Any]) -> Optional[datetime]:
        _aifstime_utc: str = values["aifstime_utc"]
        _state: str = values["state"]

        if not _state or not _aifstime_utc:
            return None

        dt = datetime.strptime(_aifstime_utc, "%Y%m%d%H%M%S")

        if _state not in STATE_TO_TIMEZONE.keys():
            return None

        timezone = pytz.timezone(STATE_TO_TIMEZONE[_state])

        dt_return = dt.replace(tzinfo=UTC).astimezone(timezone)

        return dt_return


class BOMObservationReturn(BaseConfig):
    station_code: Optional[str]
    state: str

    observations: List[BOMObserationSchema]

    _validate_state = validator("state", pre=True)(lambda x: x.strip().upper())


def get_bom_request_headers() -> Dict[str, str]:
    """Returns request headers for BOM requests"""
    return {**BOM_REQUEST_HEADERS, "User-Agent": get_random_agent()}


def get_bom_observations(observation_url: str, station_code: str) -> BOMObservationReturn:
    """Requests a BOM observation JSON endpoint and returns a schema"""
    _headers = get_bom_request_headers()

    logger.info("Fetching {}".format(observation_url))

    resp = requests.get(observation_url, headers=_headers)

    resp_object = resp.json()

    if "observations" not in resp_object:
        raise Exception("Invalid BOM return for {}".format(observation_url))

    _oo = resp_object["observations"]

    observations = BOMObservationReturn(
        **{
            "station_code": station_code,
            "state": _oo["header"][0]["state_time_zone"],
            "observations": [
                {**i, "state": _oo["header"][0]["state_time_zone"]} for i in _oo["data"]
            ],
        }
    )

    return observations


if __name__ == "__main__":
    u = "http://www.bom.gov.au/fwo/IDN60801/IDN60801.94768.json"

    r = get_bom_observations(u, "066214")

    print(r.json(indent=4))
