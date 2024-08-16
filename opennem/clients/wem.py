# pylint: disable=no-self-argument
"""OpenNEM WEM Client

Four sources:

 * balancing summary live data (from the infographic feeds)
 * balancing summary (usually delayed 3-4 days)
 * live facility generation data
 * nemweb generation data (usually delayed 3-4 days)

See the URL constants for sources and unit tests
"""

import csv
import logging
from datetime import datetime, timedelta
from io import StringIO
from typing import Any

import requests
from pydantic import ConfigDict, ValidationError, field_validator, validator

from opennem import settings
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import get_date_component, parse_date
from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger("opennem.client.wem")

# Old URL
# _AEMO_WEM_LIVE_SCADA_URL = "https://aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv"

# New URL
_AEMO_WEM_LIVE_SCADA_URL = "https://data.wa.aemo.com.au/public/infographic/facility-intervals-last96.csv"

# _AEMO_WEM_LIVE_BALANCING_URL = "https://data.wa.aemo.com.au/public/infographic/neartime/pulse.csv"
_AEMO_WEM_LIVE_BALANCING_URL = "https://aemo.com.au/aemo/data/wa/infographic/neartime/pulse.csv"

_AEMO_WEM_SCADA_URL = "https://data.wa.aemo.com.au/public/public-data/datafiles/facility-scada/facility-scada-{year}-{month}.csv"

_AEMO_WEM_BALANCING_SUMMARY_URL = (
    "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/balancing-summary-{year}.csv"
)

_AEMO_WEM2_GENERATION_URL = "https://aemo.com.au/aemo/data/wa/infographic/generation.csv"


def _wem_balancing_summary_field_alias(field_name: str) -> str:
    """Generates field aliases to map balancing summary CSV to schema"""
    return field_name.strip().upper()


def _empty_string_to_none(field_value: str | float | None) -> str | float | None:
    if not field_value:
        return None

    if field_value == "":
        return None

    return field_value


class WEMBalancingSummaryInterval(BaseConfig):
    trading_day_interval: datetime
    forecast_eoi_mw: float | None = None
    forecast_mw: float | None = None
    price: float | None = None  # some forecasts don't have a price
    forecast_nsg_mw: float | None = None
    actual_nsg_mw: float | None = None
    actual_total_generation: float | None = None

    _validator_forecast_mw = validator("forecast_mw", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_price = validator("price", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_actual_nsw = validator("actual_nsg_mw", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_actual_total_gen = validator("actual_total_generation", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_forecast_eoi_mw = validator("forecast_eoi_mw", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_forecast_nsg_mw = validator("forecast_nsg_mw", pre=True, allow_reuse=True)(_empty_string_to_none)

    @field_validator("trading_day_interval", mode="before")
    @classmethod
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(value, network=NetworkWEM)

        if not interval_time:
            raise Exception(f"Invalid APVI forecast interval: {value}")

        return interval_time

    @property
    def is_forecast(self) -> bool:
        return not self.actual_total_generation and not self.actual_nsg_mw

    model_config = ConfigDict(alias_generator=_wem_balancing_summary_field_alias)


class WEMBalancingSummarySet(BaseConfig):
    crawled_at: datetime
    live: bool = True
    intervals: list[WEMBalancingSummaryInterval]
    source_url: str | None = None
    server_latest: datetime | None = None

    @property
    def count(self) -> int:
        return len(self.intervals)


class WEMGenerationInterval(BaseConfig):
    trading_interval: datetime
    network_id: str = "WEM"
    facility_code: str
    power: float | None = None
    eoi_quantity: float | None = None
    generated_scheduled: float | None = None
    generated_non_scheduled: float | None = None

    created_by: str = "controllers.wem"
    created_at: datetime = datetime.now()

    @property
    def generated(self) -> float | None:
        if self.power:
            return self.power

        if self.generated_scheduled and self.generated_non_scheduled:
            return self.generated_scheduled + self.generated_non_scheduled

        if self.generated_non_scheduled:
            return self.generated_non_scheduled

        if self.generated_scheduled:
            return self.generated_scheduled

        return None

    _validator_power = validator("power", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_eoi_quantity = validator("eoi_quantity", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_generated_scheduled = validator("generated_scheduled", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_generated_non_scheduled = validator("generated_non_scheduled", pre=True, allow_reuse=True)(_empty_string_to_none)

    @field_validator("trading_interval", mode="before")
    @classmethod
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(value, network=NetworkWEM)

        if not interval_time:
            raise Exception(f"Invalid APVI forecast interval: {value}")

        return interval_time


class WEMFacilityIntervalSet(BaseConfig):
    crawled_at: datetime
    live: bool = True
    intervals: list[WEMGenerationInterval]
    source_url: str | None = None
    server_latest: datetime | None = None

    @property
    def count(self) -> int:
        return len(self.intervals)


_wem_session = requests.Session()
_wem_session.headers.update({"User-Agent": get_random_agent()})


class WEMFileNotFoundException(Exception):
    pass


def wem_downloader(url: str, for_date: datetime | None = None, decode_content: bool = True) -> str:
    """Downloads WEM content using the session"""
    url_params = {
        "day": get_date_component("%d", dt=for_date),
        "month": get_date_component("%m", dt=for_date),
        "year": get_date_component("%Y", dt=for_date),
    }

    _url_parsed = url.format(**url_params)

    logger.info(f"Fetching {_url_parsed}")

    response = _wem_session.get(_url_parsed, verify=settings.http_verify_ssl)

    # sometimes with the WEM delay the current
    # month isn't up
    if response.status_code == 404:
        raise WEMFileNotFoundException()

    if not response.ok:
        raise Exception(f"Get WEM facility intervals summary error: {response.status_code}")

    # @TODO mime detect and decoding
    _content = response.content.decode("utf-8")

    return _content


def parse_wem_live_balancing_summary(content: str) -> list[WEMBalancingSummaryInterval]:
    """Parses a WEM live balancing summary response into models"""
    _models = []
    csvreader = csv.DictReader(content.split("\n"))

    logger.debug("CSV has fields: {}".format(", ".join(csvreader.fieldnames)))  # type: ignore

    for _csv_rec in csvreader:
        # adapts the fields from balancing-summary history to match our schema
        _m = None

        try:
            _m = WEMBalancingSummaryInterval(**_csv_rec)
        except ValidationError as e:
            logger.error(f"Validation error for record: {e}")
            logger.debug(_csv_rec)

        if _m:
            _models.append(_m)

    logger.debug(f"Got {len(_models)} balancing summary records")

    return _models


def parse_wem_balancing_summary(content: str) -> list[WEMBalancingSummaryInterval]:
    """Parses the wem nemweb balancing summary"""
    _models = []
    csvreader = csv.DictReader(content.split("\n"))

    logger.debug("CSV has fields: {}".format(", ".join(csvreader.fieldnames)))  # type: ignore

    for _csv_rec in csvreader:
        # remap fields
        _csv_rec = {
            "TRADING_DAY_INTERVAL": _csv_rec["Trading Interval"],
            "PRICE": _csv_rec["Final Price ($/MWh)"],
            "FORECAST_NSG_MW": _csv_rec["Non-Scheduled Generation (MW)"],
            "ACTUAL_TOTAL_GENERATION": _csv_rec["Total Generation (MW)"],
            **_csv_rec,
        }

        _m = None

        try:
            _m = WEMBalancingSummaryInterval(**_csv_rec)
        except ValidationError as e:
            logger.error(f"Validation error for record: {e}")
            logger.debug(_csv_rec)

        if _m:
            _models.append(_m)

    logger.debug(f"Got {len(_models)} balancing summary records")

    return _models


def get_wem_live_balancing_summary() -> WEMBalancingSummarySet:
    """Obtains WEM live balancing summary from pulse with forecasts
    (price, generation etc.) and returns a summary set model"""
    resp = wem_downloader(_AEMO_WEM_LIVE_BALANCING_URL)

    _models = parse_wem_live_balancing_summary(resp)

    server_latest: datetime | None = None

    all_trading_intervals = list({i.trading_day_interval for i in _models if i.price is not None})

    if all_trading_intervals:
        server_latest = max(all_trading_intervals)
    else:
        logger.info("No trading intervals for in wem live balancing")

    wem_set = WEMBalancingSummarySet(
        crawled_at=datetime.now(),
        live=True,
        source_url=_AEMO_WEM_LIVE_BALANCING_URL,
        server_latest=server_latest,
        intervals=_models,
    )

    return wem_set


def get_wem_balancing_summary() -> WEMBalancingSummarySet:
    """Obtains WEM balancing summary (price, generation etc.) and returns a
    summary set model"""
    resp = wem_downloader(_AEMO_WEM_BALANCING_SUMMARY_URL)

    _models = parse_wem_balancing_summary(resp)

    server_latest: datetime | None = None

    all_trading_intervals = list({i.trading_day_interval for i in _models if i.forecast_eoi_mw is None and i.forecast_mw is None})

    if all_trading_intervals:
        server_latest = max(all_trading_intervals)

    wem_set = WEMBalancingSummarySet(
        crawled_at=datetime.now(),
        live=True,
        source_url=_AEMO_WEM_LIVE_BALANCING_URL,
        server_latest=server_latest,
        intervals=_models,
    )

    return wem_set


WEM_FACILITY_INTERVAL_FIELD_REMAP = {
    # live
    "PERIOD": "trading_interval",
    "FACILITY_CODE": "facility_code",
    "ACTUAL_MW": "power",
    # "FORECAST_EOI_MW": "forecast_load"
    # nemweb
    "Energy Generated (MWh)": "eoi_quantity",
    "Trading Interval": "trading_interval",
    "EOI Quantity (MW)": "power",
    "Facility Code": "facility_code",
}


def _remap_wem_facility_interval_field(field_name: str) -> str:
    field_name = field_name.strip()

    if field_name not in WEM_FACILITY_INTERVAL_FIELD_REMAP:
        return field_name

    return WEM_FACILITY_INTERVAL_FIELD_REMAP[field_name]


def parse_wem_facility_intervals(content: str) -> list[WEMGenerationInterval]:
    """parses the wem live generation intervals for each facility"""

    _models = []

    csvreader = csv.DictReader(content.split("\n"))

    for _csv_rec in csvreader:
        # adapts the fields from balancing-summary history to match our schema
        _csv_rec = {_remap_wem_facility_interval_field(i): k for i, k in _csv_rec.items()}

        # @NOTE do wem energy here
        if "power" in _csv_rec and _csv_rec["power"] and float(_csv_rec["power"]) > 0:
            _csv_rec["eoi_quantity"] = str(float(_csv_rec["power"]) / 2.0)

        _m = None

        try:
            _m = WEMGenerationInterval(**_csv_rec)
        except ValidationError as e:
            logger.error(f"Validation error for record: {e}")
            logger.debug(_csv_rec)

        if _m:
            _models.append(_m)

    logger.debug(f"Got {len(_models)} facility interval records")

    return _models


def get_wem_live_facility_intervals(
    trim_intervals: bool = False, from_interval: datetime | None = None
) -> WEMFacilityIntervalSet:
    """Obtains WEM live facility intervals from infogrphic feeds"""
    content = wem_downloader(_AEMO_WEM_LIVE_SCADA_URL)
    _models = parse_wem_facility_intervals(content)

    server_latest: datetime | None = None

    all_trading_intervals = list({i.trading_interval for i in _models})

    if all_trading_intervals:
        server_latest = max(all_trading_intervals)

    if trim_intervals and server_latest:
        _models = [
            i
            for i in _models
            if i.trading_interval == server_latest or (i.trading_interval == server_latest - timedelta(minutes=30))
        ]

    elif from_interval and server_latest:
        _models = [i for i in _models if i.trading_interval >= from_interval]

    wem_set = WEMFacilityIntervalSet(
        crawled_at=datetime.now(),
        live=True,
        intervals=_models,
        source_url=_AEMO_WEM_LIVE_SCADA_URL,
        server_latest=server_latest,
    )

    return wem_set


def get_wem_facility_intervals(from_date: datetime | None = None) -> WEMFacilityIntervalSet:
    """Obtains WEM facility intervals from NEM web. Will default to most recent date

    @TODO not yet smart enough to know if it should check current or archive
    """
    content: str | None = None

    try:
        content = wem_downloader(_AEMO_WEM_SCADA_URL, from_date)
    except WEMFileNotFoundException:
        _now = datetime.now()
        from_date = _now - timedelta(days=30)
        content = wem_downloader(_AEMO_WEM_SCADA_URL, from_date)

    if not content:
        raise Exception("No content for wem facility intervals")

    _models = parse_wem_facility_intervals(content)

    server_latest: datetime | None = None

    all_trading_intervals = list({i.trading_interval for i in _models})

    if all_trading_intervals:
        server_latest = max(all_trading_intervals)

    wem_set = WEMFacilityIntervalSet(
        crawled_at=datetime.now(),
        live=False,
        source_url=_AEMO_WEM_SCADA_URL,
        intervals=_models,
        server_latest=server_latest,
    )

    return wem_set


def get_wem2_live_generation_models() -> list[WEMGenerationInterval]:
    """Gets the latest WEM live generation CSV"""
    resp = wem_downloader(_AEMO_WEM2_GENERATION_URL, decode_content=True)

    if not isinstance(resp, str):
        raise Exception("Invalid response from WEM2 generation - not string")

    models = []

    field_names = ["PARTICIPANT_CODE", "FACILITY_CODE", "MAX_GEN_CAPACITY"]
    field_names += [f"I{str(i).zfill(2)}" for i in range(1, 49)]
    field_names += ["AS_AT"]

    facility_reader = csv.DictReader(StringIO(resp), fieldnames=field_names)

    # Skip the header
    next(facility_reader)

    latest_interval = None

    for facility_record in facility_reader:
        if facility_record["AS_AT"]:
            parse_as_at = parse_date(facility_record["AS_AT"], timezone=NetworkWEM.get_fixed_offset())

            if parse_as_at:
                latest_interval = parse_as_at
                logger.info(f"Latest interval is {latest_interval} found via AS_AT")
            else:
                raise Exception(f"Invalid AS_AT date: {facility_record["AS_AT"]}")

        if not latest_interval:
            raise Exception("No latest interval found")

        facility_code = facility_record["FACILITY_CODE"]

        for interval_number in range(1, 49):
            interval_field = f"I{str(interval_number).zfill(2)}"

            if interval_field not in facility_record:
                logger.error(f"Interval {interval_field} not in record for facility {facility_code}")
                continue

            generation_value = float(facility_record[interval_field]) if facility_record[interval_field] else 0
            interval_value = latest_interval - timedelta(minutes=5 * (interval_number - 1))

            model_dict = {
                "trading_interval": interval_value,
                "facility_code": facility_code,
                "power": generation_value,
                "eoi_quantity": generation_value / 12,
            }

            model = WEMGenerationInterval(**model_dict)

            models.append(model)

    return models


def get_wem2_live_facility_intervals(
    trim_intervals: bool = False, from_interval: datetime | None = None
) -> WEMFacilityIntervalSet:
    """Obtains WEM v2 live facility intervals from infogrphic feeds"""
    _models = get_wem2_live_generation_models()

    server_latest: datetime | None = None

    all_trading_intervals = list({i.trading_interval for i in _models})

    if all_trading_intervals:
        server_latest = max(all_trading_intervals)

    if trim_intervals and server_latest:
        _models = [
            i
            for i in _models
            if i.trading_interval == server_latest or (i.trading_interval == server_latest - timedelta(minutes=30))
        ]

    elif from_interval and server_latest:
        _models = [i for i in _models if i.trading_interval >= from_interval]

    wem_set = WEMFacilityIntervalSet(
        crawled_at=datetime.now(),
        live=True,
        intervals=_models,
        source_url=_AEMO_WEM2_GENERATION_URL,
        server_latest=server_latest,
    )

    return wem_set


# debug entry point
if __name__ == "__main__":
    # m = get_wem_facility_intervals(live=False)

    # m = get_wem_facility_intervals()

    # with open("wem.json", "w") as fh:
    #     fh.write(m.json(indent=4))

    from pprint import pprint

    balancing_set = get_wem_live_balancing_summary()

    for model in balancing_set.intervals:
        pprint(dict(model))
        # print(dict(models[0]))

    # with open("wem-live.json", "w") as fh:
    # fh.write(m.json(indent=4))
