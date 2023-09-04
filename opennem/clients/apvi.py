"""APVI Client for Rooftop Data

"""
import logging
import urllib.parse as urlparse
from datetime import date, datetime
from json.decoder import JSONDecodeError
from typing import Any
from urllib.parse import urlencode

from pydantic import ValidationError, validator

from opennem import settings
from opennem.core.normalizers import is_number
from opennem.importer.rooftop import ROOFTOP_CODE
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_today_opennem, parse_date
from opennem.utils.http import http
from opennem.utils.version import get_version

logger = logging.getLogger(__name__)

# APVI_DATA_URI = "https://pv-map.apvi.org.au/data"

APVI_DATA_URI = "https://pv-map.apvi.org.au/api/v2/2-digit/{date}.json"

APVI_NETWORK_CODE = "APVI"

APVI_DATE_QUERY_FORMAT = "%Y-%m-%d"

APVI_EARLIEST_DATE = "2013-05-07"

# @TODO remove this eventually
STATE_POSTCODE_PREFIXES = {
    "NSW": "2",
    "VIC": "3",
    "QLD": "4",
    "SA": "5",
    "WA": "6",
    "TAS": "7",
    "NT": "0",
}

POSTCODE_STATE_PREFIXES = {
    "2": "NSW",
    "3": "VIC",
    "4": "QLD",
    "5": "SA",
    "6": "WA",
    "7": "TAS",
    "0": "NT",
}

WA_NON_SWIS = ["66", "67"]


def get_state_for_prefix(prefix: str) -> str:
    """Returns a state for a prefix"""
    if not is_number(prefix):
        raise Exception(f"get_state_for_prefix: {prefix} is not a number")

    if prefix[:1] not in POSTCODE_STATE_PREFIXES.keys():
        raise Exception(f"get_state_for_prefix: could not find state for prefix {prefix}")

    return POSTCODE_STATE_PREFIXES[prefix[:1]]


def get_apvi_uri(date: date | None = None) -> str:
    """Get the APVI URL and set token from config"""

    if not date:
        date = get_today_opennem().date()

    if date == get_today_opennem().date():
        date = "today"  # type: ignore

    url = APVI_DATA_URI.format(date=date)

    params = {}

    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))

    if settings.apvi_token:
        params["access_token"] = settings.apvi_token
        query.update(params)

    url_parts[4] = urlencode(query)

    return urlparse.urlunparse(url_parts)


class APVIForecastInterval(BaseConfig):
    trading_interval: datetime
    network_id: str = APVI_NETWORK_CODE
    state: str | None
    facility_code: str | None
    generated: float | None
    eoi_quantity: float | None

    _validate_state = validator("state", pre=True, allow_reuse=True)(lambda x: x.strip().upper() if x else None)

    @validator("trading_interval", pre=True)
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(
            value,
            dayfirst=False,
            yearfirst=True,
        )

        if not interval_time:
            raise Exception(f"Invalid APVI forecast interval: {value}")

        # All APVI data is in NEM time
        interval_time = interval_time.astimezone(NetworkNEM.get_timezone())  # type: ignore

        return interval_time

    @validator("facility_code", always=True, pre=True)
    def _validate_facility_code(cls, value: Any, values: dict[str, Any]) -> str | None:
        """Generate an OpenNEM derived facility code for APVI facilities"""
        state = values.get("state", None)

        if not state:
            return None

        return f"{ROOFTOP_CODE}_{APVI_NETWORK_CODE}_{state.upper()}"

    @validator("eoi_quantity", always=True, pre=True)
    def _validate_eoi_quantity(cls, value: Any, values: dict[str, Any]) -> float | None:
        """Calculates energy value"""
        generated = values["generated"]
        energy_quantity: float | None = None

        if generated and is_number(generated):
            energy_quantity = float(generated) / 4

        return energy_quantity


class APVIStateRooftopCapacity(BaseConfig):
    state: str
    capacity_registered: float
    facility_code: str | None
    unit_number: int | None

    @validator("facility_code", always=True, pre=True)
    def _validate_facility_code(cls, value: Any, values: dict[str, Any]) -> str:
        """Generate an OpenNEM derived facility code for APVI facilities"""
        state = values["state"]

        return f"{ROOFTOP_CODE}_{APVI_NETWORK_CODE}_{state.upper()}"


class APVIForecastSet(BaseConfig):
    crawled_at: datetime | None
    intervals: list[APVIForecastInterval]
    server_latest: datetime | None
    capacities: list[APVIStateRooftopCapacity] | None


_apvi_request_session = http

_apvi_request_session.headers.update({"User-Agent": f"OpenNEM/{get_version()}"})


def get_apvi_rooftop_data(day: date | None = None) -> APVIForecastSet | None:
    """Obtains and parses APVI forecast data"""

    apvi_endpoint_url = get_apvi_uri(date=day)

    logger.info(f"Getting APVI data for day {day} from {apvi_endpoint_url}")

    _resp = _apvi_request_session.get(apvi_endpoint_url, data={"day": day})

    if not _resp.ok:
        logger.error(f"Invalid APVI Return: {_resp.status_code}")
        return None

    _resp_json = None

    try:
        _resp_json = _resp.json()
    except JSONDecodeError as e:
        logger.error(f"Error decoding APVI response: {e}")
        return None

    _required_keys = ["performance", "capacity", "load"]

    for _req_key in _required_keys:
        if _req_key not in _resp_json:
            logger.error(f"Invalid APVI response: {_req_key} field not found")
            return None

    postcode_gen = _resp_json["performance"]
    postcode_capacity = _resp_json["capacity"]
    installations = _resp_json.get("installations", None)

    # brisbane has no DST so its effectively NEM time
    _run_at = get_today_opennem()
    _interval_records = []

    grouped_records = {}

    for postcode_prefix, record in postcode_gen.items():
        state = POSTCODE_STATE_PREFIXES.get(postcode_prefix[:1])

        if state not in grouped_records:
            grouped_records[state] = {}

        for interval, value in record.items():
            if interval not in grouped_records[state]:
                grouped_records[state][interval] = 0

            grouped_records[state][interval] += value / 100 * postcode_capacity[postcode_prefix]

    for state, record in grouped_records.items():
        for interval, value in record.items():
            _interval_records.append(
                APVIForecastInterval(trading_interval=interval, state=state, generated=value, eoi_quantity=value / 4)
            )

    _state_capacities = {}

    # Calcualte state capacities
    for postcode_prefix, capacity_val in postcode_capacity.items():
        for state, prefix in STATE_POSTCODE_PREFIXES.items():
            if state not in _state_capacities:
                _state_capacities[state] = 0

            if postcode_prefix.startswith(prefix):
                _state_capacities[state] += capacity_val

    # derive state capacity models
    _state_capacity_models = []

    for state, state_capacity in _state_capacities.items():
        capacity_registered = state_capacity
        unit_number = None

        if installations and state.lower() in installations:
            unit_number = installations[state.lower()]

        _state_capacity_models.append(
            APVIStateRooftopCapacity(state=state, capacity_registered=capacity_registered, unit_number=unit_number)
        )

    apvi_server_latest: datetime | None = None

    trading_intervals = list({i.trading_interval for i in _interval_records})

    if trading_intervals:
        apvi_server_latest = max(trading_intervals)

    apvi_forecast_set = APVIForecastSet(crawled=_run_at, intervals=_interval_records, capacities=_state_capacity_models)

    try:
        apvi_forecast_set.server_latest = apvi_server_latest
    except ValidationError:
        logger.error(f"APVI validation error for server_latest: {apvi_server_latest} <{repr(apvi_server_latest)}>")

    return apvi_forecast_set


if __name__ == "__main__":
    cr = get_apvi_rooftop_data()

    if not cr:
        raise Exception("Invalid APVI Data")

    with open("apvi.json", "w") as fh:
        fh.write(cr.json(indent=4))
