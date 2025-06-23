"""APVI Client for Rooftop Data"""

import logging
import urllib.parse as urlparse
from datetime import date, datetime
from json.decoder import JSONDecodeError
from typing import Any
from urllib.parse import urlencode

import polars as pl
from pydantic import ValidationError, field_validator

from opennem import settings
from opennem.core.normalizers import is_number
from opennem.importer.rooftop import ROOFTOP_CODE
from opennem.schema.core import BaseConfig
from opennem.schema.field_types import RoundedFloat4
from opennem.utils.dates import get_today_opennem, parse_date
from opennem.utils.httpx import httpx_factory
from opennem.utils.version import get_version

logger = logging.getLogger(__name__)

# APVI_DATA_URI = "https://pv-map.apvi.org.au/data"

APVI_DATA_URI = "https://pv-map.apvi.org.au/api/v2/2-digit/{date}.json"

APVI_CAPACITY_URL = "https://pv-map.apvi.org.au/data/postcode/monthly/capacity/{postcode}"

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
    interval: datetime
    network_id: str = APVI_NETWORK_CODE
    state: str | None = None
    facility_code: str | None = None
    generated: RoundedFloat4 | None = None
    energy: RoundedFloat4 | None = None

    @field_validator("state", mode="before")
    def _validate_state(cls, value: str | None) -> str | None:
        """Validate and format the state field."""
        return value.strip().upper() if value else None

    @field_validator("interval", mode="before")
    def _validate_trading_interval(cls, value: Any) -> datetime:
        """Validate and parse the trading interval."""
        interval_time = parse_date(
            value,
            dayfirst=False,
            yearfirst=True,
        )

        if not interval_time:
            raise Exception(f"Invalid APVI forecast interval: {value}")

        return interval_time.replace(tzinfo=None)


class APVIStateRooftopCapacity(BaseConfig):
    state: str
    month: date | None = None
    capacity_registered: float
    facility_code: str | None = None
    unit_number: int | None = None

    @field_validator("facility_code", mode="before")
    def _validate_facility_code(cls, values: dict[str, Any]) -> str:
        """Generate an OpenNEM derived facility code for APVI facilities."""
        state = values["state"]

        return f"{ROOFTOP_CODE}_{APVI_NETWORK_CODE}_{state.upper()}"


class APVIForecastSet(BaseConfig):
    crawled_at: datetime | None = None
    intervals: list[APVIForecastInterval]
    server_latest: datetime | None = None
    capacities: list[APVIStateRooftopCapacity] | None = None


_apvi_request_session = httpx_factory()

_apvi_request_session.headers.update({"User-Agent": f"OpenNEM/{get_version()}"})


async def get_apvi_rooftop_data(day: date | None = None) -> APVIForecastSet | None:
    """Obtains and parses APVI forecast data"""

    apvi_endpoint_url = get_apvi_uri(date=day)

    logger.info(f"Getting APVI data for day {day} from {apvi_endpoint_url}")

    _resp = await _apvi_request_session.request("GET", apvi_endpoint_url, data={"day": day})

    if _resp.is_error:
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
            _interval_records.append(APVIForecastInterval(interval=interval, state=state, generated=value, energy=value / 4))

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

    trading_intervals = list({i.interval for i in _interval_records})

    if trading_intervals:
        apvi_server_latest = max(trading_intervals)

    apvi_forecast_set = APVIForecastSet(crawled_at=_run_at, intervals=_interval_records, capacities=_state_capacity_models)

    try:
        apvi_forecast_set.server_latest = apvi_server_latest
    except ValidationError:
        logger.error(f"APVI validation error for server_latest: {apvi_server_latest} <{repr(apvi_server_latest)}>")

    return apvi_forecast_set


async def get_apvi_rooftop_capacity() -> pl.DataFrame:
    """Get the APVI rooftop capacity for a postcode"""

    all_data = pl.DataFrame()

    for postcode_prefix, region in POSTCODE_STATE_PREFIXES.items():
        state_df = pl.DataFrame()
        postcode_state = f"{postcode_prefix}000"

        apvi_capacity_url = APVI_CAPACITY_URL.format(postcode=postcode_state)

        logger.info(f"Getting APVI capacity for {postcode_prefix} {region} {apvi_capacity_url}")
        response = await _apvi_request_session.request("GET", apvi_capacity_url)

        if response.is_error:
            logger.error(f"Invalid APVI Return: {response.status_code}")
            logger.debug(response.text)
            continue

        response_json = response.json()

        if postcode_state not in response_json:
            logger.error(f"Invalid APVI Return: {postcode_state} not found in {response_json}")
            continue

        state_df = pl.DataFrame(response_json[postcode_state])

        state_df = state_df.with_columns(pl.col("month").str.strptime(pl.Date, "%Y-%m"))

        # add field facility_code to dataframe
        state_df = state_df.with_columns(
            pl.lit(f"ROOFTOP_APVI_{region.upper()}").alias("facility_code"), pl.lit(region.upper()).alias("state")
        )

        # sum the capacity columns
        capacity_columns = [
            "2hf",
            "2hf_4hf",
            "4hf_6hf",
            "6hf_9hf",
            "9hf_14",
            "14_25",
            "25_50",
            "50_100",
            "100_5000",
            # "5000_30000",
            # "30000",
        ]
        state_df = state_df.with_columns(pl.sum_horizontal(capacity_columns).alias("capacity_registered"))

        # drop the individual capacity columns to simplify output
        state_df = state_df.drop(capacity_columns)
        # also drop the large capacity columns we're not summing
        state_df = state_df.drop(["5000_30000", "30000"])

        all_data = all_data.vstack(state_df)

    # Sort by facility_code then month ascending
    all_data = all_data.sort(["facility_code", "month"])

    # Calculate cumulative capacity for each facility_code
    all_data = all_data.with_columns(pl.col("capacity_registered").cum_sum().over("facility_code").alias("capacity_registered"))

    return all_data


if __name__ == "__main__":
    import asyncio

    df = asyncio.run(get_apvi_rooftop_capacity())

    if df.is_empty():
        raise Exception("Invalid APVI Data")

    # print the dataframe
    print(df.head(50))
