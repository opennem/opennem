"""OpenNEM BoM Client"""

import logging
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests
from pydantic import validator

from opennem.schema.core import BaseConfig
from opennem.utils.http import attach_proxy, mount_retry_adaptor, mount_timeout_adaptor, retry_strategy_on_permission_denied
from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger("opennem.clients.bom")

BOM_REQUEST_HEADERS = {
    "Host": "www.bom.gov.au",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    ),
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


_bom_req_session = requests.Session()

attach_proxy(_bom_req_session)

mount_retry_adaptor(_bom_req_session)
_bom_req_session.mount("http://", retry_strategy_on_permission_denied)  # type: ignore
_bom_req_session.mount("https://", retry_strategy_on_permission_denied)  # type: ignore

mount_timeout_adaptor(_bom_req_session)


def _clean_bom_text_field(field_val: str) -> str | None:
    """Takes the messy BOM string fields and cleans them up"""
    _v = field_val.strip().replace("-", "")

    if len(_v) == 0 or not _v:
        return None

    return _v


class BOMObserationSchema(BaseConfig):
    state: str
    aifstime_utc: str
    observation_time: datetime | None = None
    apparent_t: float | None = None
    air_temp: float
    press_qnh: float | None = None
    wind_dir: str | None = None
    wind_spd_kmh: float | None = None
    gust_kmh: float | None = None
    rel_hum: float | None = None
    cloud: str | None = None
    cloud_type: str | None = None

    _validate_cloud = validator("cloud", pre=True, allow_reuse=True)(_clean_bom_text_field)
    _validate_cloud_type = validator("cloud_type", pre=True, allow_reuse=True)(_clean_bom_text_field)

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("observation_time", always=True, pre=True)
    def _validate_observation_time(cls, value: str, values: dict[str, Any]) -> datetime | None:
        _aifstime_utc: str = values["aifstime_utc"]
        _state: str = values["state"]

        if not _state or not _aifstime_utc:
            return None

        dt = datetime.strptime(_aifstime_utc, "%Y%m%d%H%M%S")

        if _state not in STATE_TO_TIMEZONE.keys():
            return None

        tz = ZoneInfo(STATE_TO_TIMEZONE[_state])

        dt_return = dt.replace(tzinfo=UTC).astimezone(tz)

        return dt_return


class BOMObservationReturn(BaseConfig):
    station_code: str | None = None
    state: str

    observations: list[BOMObserationSchema]

    _validate_state = validator("state", pre=True)(lambda x: x.strip().upper())


def get_bom_request_headers() -> dict[str, str]:
    """Returns request headers for BOM requests"""
    return {**BOM_REQUEST_HEADERS, "User-Agent": get_random_agent()}


class BOMParsingException(Exception):
    pass


def get_bom_observations(observation_url: str, station_code: str) -> BOMObservationReturn:
    """Requests a BOM observation JSON endpoint and returns a schema"""
    _headers = get_bom_request_headers()

    logger.info(f"Fetching {observation_url}")

    resp = _bom_req_session.get(observation_url, headers=_headers)

    resp_object = None

    if not resp.ok or resp.status_code == 403:
        raise Exception(f"BoM client request exception: {resp.status_code}")

    try:
        resp_object = resp.json()
    except Exception:
        raise BOMParsingException(
            f"Error parsing BOM response: bad json. Status: {resp.status_code}. Content length: {len(resp.content)}"
        ) from None

    if "observations" not in resp_object:
        raise BOMParsingException(f"Invalid BOM return for {observation_url}")

    _oo = resp_object["observations"]

    observations = BOMObservationReturn(
        **{
            "station_code": station_code,
            "state": _oo["header"][0]["state_time_zone"],
            "observations": [
                {**i, "state": _oo["header"][0]["state_time_zone"]}
                for i in _oo["data"]
                if "air_temp" in i and i["air_temp"] is not None
            ],
        }
    )

    return observations


if __name__ == "__main__":
    u = "http://www.bom.gov.au/fwo/IDN60801/IDN60801.94768.json"

    r = get_bom_observations(u, "066214")

    for i in r.observations:
        print(f"{i.observation_time}: {i.air_temp} {i.apparent_t}")
