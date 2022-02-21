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
from typing import Any, Dict, List, Optional, Union

import requests
from pydantic import ValidationError, validator

from opennem import settings
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import get_date_component, parse_date
from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger("opennem.client.wem")

_AEMO_WEM_LIVE_SCADA_URL = (
    "https://aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv"
)

_AEMO_WEM_LIVE_BALANCING_URL = "https://data.wa.aemo.com.au/public/infographic/neartime/pulse.csv"

_AEMO_WEM_SCADA_URL = "https://data.wa.aemo.com.au/public/public-data/datafiles/facility-scada/facility-scada-{year}-{month}.csv"

_AEMO_WEM_BALANCING_SUMMARY_URL = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/balancing-summary-{year}.csv"


def _wem_balancing_summary_field_alias(field_name: str) -> str:
    """Generates field aliases to map balancing summary CSV to schema"""
    return field_name.strip().upper()


def _empty_string_to_none(field_value: Optional[Union[str, float]]) -> Optional[Union[str, float]]:
    if not field_value:
        return None

    if field_value == "":
        return None

    return field_value


class WEMBalancingSummaryInterval(BaseConfig):
    trading_day_interval: datetime
    forecast_eoi_mw: Optional[float]
    forecast_mw: Optional[float]
    price: Optional[float]  # some forecasts don't have a price
    forecast_nsg_mw: Optional[float]
    actual_nsg_mw: Optional[float]
    actual_total_generation: Optional[float]

    _validator_price = validator("price", pre=True, allow_reuse=True)(_empty_string_to_none)

    _validator_actual_nsw = validator("actual_nsg_mw", pre=True, allow_reuse=True)(
        _empty_string_to_none
    )

    _validator_actual_total_gen = validator("actual_total_generation", pre=True, allow_reuse=True)(
        _empty_string_to_none
    )

    _validator_forecast_eoi_mw = validator("forecast_eoi_mw", pre=True, allow_reuse=True)(
        _empty_string_to_none
    )

    _validator_forecast_nsg_mw = validator("forecast_nsg_mw", pre=True, allow_reuse=True)(
        _empty_string_to_none
    )

    @validator("trading_day_interval", pre=True)
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(value, network=NetworkWEM)

        if not interval_time:
            raise Exception(f"Invalid APVI forecast interval: {value}")

        return interval_time

    @property
    def is_forecast(self) -> bool:
        return not self.actual_total_generation and not self.actual_nsg_mw

    class Config:
        alias_generator = _wem_balancing_summary_field_alias


class WEMBalancingSummarySet(BaseConfig):
    crawled_at: datetime
    live: bool = True
    intervals: List[WEMBalancingSummaryInterval]
    source_url: Optional[str]

    @property
    def count(self) -> int:
        return len(self.intervals)


class WEMGenerationInterval(BaseConfig):
    trading_interval: datetime
    network_id: str = "WEM"
    facility_code: str
    power: Optional[float]
    eoi_quantity: Optional[float]
    generated_scheduled: Optional[float]
    generated_non_scheduled: Optional[float]

    created_by: str = "controllers.wem"
    created_at: datetime = datetime.now()

    @property
    def generated(self) -> Optional[float]:
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

    _validator_eoi_quantity = validator("eoi_quantity", pre=True, allow_reuse=True)(
        _empty_string_to_none
    )

    _validator_generated_scheduled = validator("generated_scheduled", pre=True, allow_reuse=True)(
        _empty_string_to_none
    )

    _validator_generated_non_scheduled = validator(
        "generated_non_scheduled", pre=True, allow_reuse=True
    )(_empty_string_to_none)

    @validator("trading_interval", pre=True)
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(value, network=NetworkWEM)

        if not interval_time:
            raise Exception(f"Invalid APVI forecast interval: {value}")

        return interval_time


class WEMFacilityIntervalSet(BaseConfig):
    crawled_at: datetime
    live: bool = True
    intervals: List[WEMGenerationInterval]
    source_url: Optional[str]

    @property
    def count(self) -> int:
        return len(self.intervals)


_wem_session = requests.Session()
_wem_session.headers.update({"User-Agent": get_random_agent()})


class WEMFileNotFoundException(Exception):
    pass


def wem_downloader(url: str, for_date: Optional[datetime] = None) -> str:
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
        raise Exception(
            "Get WEM facility intervals summary error: {}".format(response.status_code)
        )

    # @TODO mime detect and decoding
    _content = response.content.decode("utf-8")

    return _content


def parse_wem_live_balancing_summary(content: str) -> List[WEMBalancingSummaryInterval]:
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
            logger.error("Validation error for record: {}".format(e))
            logger.debug(_csv_rec)

        if _m:
            _models.append(_m)

    logger.debug(f"Got {len(_models)} balancing summary records")

    return _models


def parse_wem_balancing_summary(content: str) -> List[WEMBalancingSummaryInterval]:
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
            logger.error("Validation error for record: {}".format(e))
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

    wem_set = WEMBalancingSummarySet(
        crawled_at=datetime.now(),
        live=True,
        source_url=_AEMO_WEM_LIVE_BALANCING_URL,
        intervals=_models,
    )

    return wem_set


def get_wem_balancing_summary() -> WEMBalancingSummarySet:
    """Obtains WEM balancing summary (price, generation etc.) and returns a
    summary set model"""
    resp = wem_downloader(_AEMO_WEM_BALANCING_SUMMARY_URL)

    _models = parse_wem_balancing_summary(resp)

    wem_set = WEMBalancingSummarySet(
        crawled_at=datetime.now(),
        live=True,
        source_url=_AEMO_WEM_LIVE_BALANCING_URL,
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


def parse_wem_facility_intervals(content: str) -> List[WEMGenerationInterval]:
    """parses the wem live generation intervals for each facility"""

    _models = []

    csvreader = csv.DictReader(content.split("\n"))

    for _csv_rec in csvreader:
        # adapts the fields from balancing-summary history to match our schema
        _csv_rec = {_remap_wem_facility_interval_field(i): k for i, k in _csv_rec.items()}

        # @NOTE do wem energy here
        if "power" in _csv_rec and _csv_rec["power"] and float(_csv_rec["power"]) > 0:
            _csv_rec["eoi_quantity"] = float(_csv_rec["power"]) / 2.0

        _m = None

        try:
            _m = WEMGenerationInterval(**_csv_rec)
        except ValidationError as e:
            logger.error("Validation error for record: {}".format(e))
            logger.debug(_csv_rec)

        if _m:
            _models.append(_m)

    logger.debug(f"Got {len(_models)} facility interval records")

    return _models


def get_wem_live_facility_intervals() -> WEMFacilityIntervalSet:
    """Obtains WEM live facility intervals from infogrphic feeds"""
    content = wem_downloader(_AEMO_WEM_LIVE_SCADA_URL)
    _models = parse_wem_facility_intervals(content)

    wem_set = WEMFacilityIntervalSet(
        crawled_at=datetime.now(),
        live=True,
        intervals=_models,
        source_url=_AEMO_WEM_LIVE_SCADA_URL,
    )

    return wem_set


def get_wem_facility_intervals(from_date: Optional[datetime] = None) -> WEMFacilityIntervalSet:
    """Obtains WEM facility intervals from NEM web. Will default to most recent date

    @TODO not yet smart enough to know if it should check current or archive
    """
    content: Optional[str] = None

    try:
        content = wem_downloader(_AEMO_WEM_SCADA_URL, from_date)
    except WEMFileNotFoundException:
        _now = datetime.now()
        from_date = _now - timedelta(days=30)
        content = wem_downloader(_AEMO_WEM_SCADA_URL, from_date)

    if not content:
        raise Exception("No content for wem facility intervals")

    _models = parse_wem_facility_intervals(content)

    wem_set = WEMFacilityIntervalSet(
        crawled_at=datetime.now(), live=False, source_url=_AEMO_WEM_SCADA_URL, intervals=_models
    )

    return wem_set


# debug entry point
if __name__ == "__main__":
    # m = get_wem_facility_intervals(live=False)

    # m = get_wem_facility_intervals()

    # with open("wem.json", "w") as fh:
    #     fh.write(m.json(indent=4))

    m = get_wem_live_facility_intervals()

    with open("wem-live.json", "w") as fh:
        fh.write(m.json(indent=4))
