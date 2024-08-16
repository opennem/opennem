"""OpenNEM BoM Client"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from pydantic import BeforeValidator, model_validator

from opennem.schema.core import BaseConfig
from opennem.utils.httpx import httpx_factory
from opennem.utils.timezone import get_timezone_for_state

logger = logging.getLogger("opennem.clients.bom")

# BoM model utils


def _clean_bom_text_field(field_val: str | None) -> str | None:
    """Takes the messy BOM string fields and cleans them up


    example input: "-"
    example output: None
    """
    if not field_val:
        return None

    _v = field_val.strip().replace("-", "")

    if not _v:
        return None

    return _v


def _validate_observation_time(values: dict[str, Any]) -> datetime:
    _aifstime_utc: str = values["aifstime_utc"]
    _state: str = values["state"]

    if not _state or not _aifstime_utc:
        raise ValueError("Missing state or aifstime_utc")

    dt = datetime.strptime(_aifstime_utc, "%Y%m%d%H%M%S")

    tz = ZoneInfo(get_timezone_for_state(_state))

    dt_return = dt.replace(tzinfo=UTC).astimezone(tz)

    return dt_return


# BoM Types

BoMState = Annotated[str, BeforeValidator(lambda x: x.strip().upper())]
BoMCleanString = Annotated[str | None, BeforeValidator(_clean_bom_text_field)]
BoMObservationDateTime = Annotated[datetime, BeforeValidator(_validate_observation_time)]


# BoM Schemas
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
    cloud: BoMCleanString | None = None
    cloud_type: BoMCleanString | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_observation_time(cls, data: Any) -> Any:
        data["observation_time"] = _validate_observation_time(data)
        return data


class BOMObservationReturn(BaseConfig):
    station_code: str | None = None
    state: BoMState

    observations: list[BOMObserationSchema]


class BOMParsingException(Exception):
    pass


async def get_bom_observations(observation_url: str, station_code: str) -> BOMObservationReturn:
    """Requests a BOM observation JSON endpoint and returns a schema"""

    logger.info(f"Fetching {observation_url}")

    async with httpx_factory(mimic_browser=True, proxy=False) as http:
        response = await http.get(observation_url)

    if response.status_code == 403:
        raise Exception(f"BoM client request exception: {response.status_code} - {response.text}")

    try:
        resp_object = response.json()
    except Exception:
        raise BOMParsingException(
            f"Error parsing BOM response: bad json. Status: {response.status_code}. Content length: {len(response.content)}"
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
    import asyncio

    u = "http://www.bom.gov.au/fwo/IDN60801/IDN60801.94768.json"

    r = asyncio.run(get_bom_observations(u, "066214"))

    for i in r.observations:
        print(f"{i.observation_time}: {i.air_temp} {i.apparent_t}")
