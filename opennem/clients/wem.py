"""OpenNEM WEM Client


"""

import csv
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from pydantic import validator

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

_AEMO_WEM_BALANCING_SUMMARY = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/balancing-summary-{year}.csv"


def _wem_balancing_summary_field_alias(field_name: str) -> str:
    """Generates field aliases to map balancing summary CSV to schema"""
    return field_name.strip().upper()


class WEMBalancingSummaryInterval(BaseConfig):
    trading_day_interval: datetime
    forecast_eoi_mw: Optional[float]
    forecast_mw: Optional[float]
    price: float
    forecast_nsg_mw: float
    actual_nsg_mw: Optional[float]
    actual_total_generation: Optional[float]

    _validator_actual_nsw = validator("actual_nsg_mw", pre=True, allow_reuse=True)(
        lambda x: None if x == "" else x
    )

    _validator_actual_total_gen = validator("actual_total_generation", pre=True, allow_reuse=True)(
        lambda x: None if x == "" else x
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

    _validator_power = validator("power", pre=True, allow_reuse=True)(
        lambda x: None if x == "" else x
    )

    _validator_eoi_quantity = validator("eoi_quantity", pre=True, allow_reuse=True)(
        lambda x: None if x == "" else x
    )

    _validator_generated_scheduled = validator("generated_scheduled", pre=True, allow_reuse=True)(
        lambda x: None if x == "" else x
    )

    _validator_generated_non_scheduled = validator(
        "generated_non_scheduled", pre=True, allow_reuse=True
    )(lambda x: None if x == "" else x)

    @validator("trading_interval", pre=True)
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(value, network=NetworkWEM)

        if not interval_time:
            raise Exception(f"Invalid APVI forecast interval: {value}")

        return interval_time

    @validator("eoi_quantity", always=True, pre=True)
    def _validate_eoi_quantity(cls, value: Any, values: Dict[str, Any]) -> Optional[float]:
        if "eoi_quantity" in values and values["eoi_quantity"]:
            return values["eoi_quantity"]

        if "generated" in values:
            _generated = values["generated"]
            return _generated / 2


class WEMFacilityIntervalSet(BaseConfig):
    crawled_at: datetime
    live: bool = True
    intervals: List[WEMGenerationInterval]

    @property
    def count(self) -> int:
        return len(self.intervals)


_wem_session = requests.Session()
_wem_session.headers.update({"User-Agent": get_random_agent()})


def get_wem_live_balancing_summary(live: bool = True) -> WEMBalancingSummarySet:
    """Obtains WEM balancing summary (price, generation etc.) and returns a
    summary set model"""
    url = _AEMO_WEM_BALANCING_SUMMARY

    if live:
        url = _AEMO_WEM_LIVE_BALANCING_URL

    logger.info(f"Fetching {url}")

    req = _wem_session.get(url)

    if not req.ok:
        raise Exception("Get wem live balancing summary error: {}".format(req.status_code))

    _models = []

    csvreader = csv.DictReader(req.content.decode("utf-8").split("\n"))

    for _csv_rec in csvreader:
        # adapts the fields from balancing-summary history to match our schema
        if not live:
            _csv_rec = {
                "TRADING_DAY_INTERVAL": _csv_rec["Trading Interval"],
                "PRICE": _csv_rec["Final Price ($/MWh)"],
                "FORECAST_NSG_MW": _csv_rec["Non-Scheduled Generation (MW)"],
                "ACTUAL_TOTAL_GENERATION": _csv_rec["Total Generation (MW)"],
                **_csv_rec,
            }

        _models.append(WEMBalancingSummaryInterval(**_csv_rec))

    logger.debug(f"Got {len(_models)} balancing summary records")

    wem_set = WEMBalancingSummarySet(crawled_at=datetime.now(), live=live, intervals=_models)

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


def get_wem_facility_intervals(live: bool = True) -> WEMFacilityIntervalSet:
    """Obtains WEM facility intervals either from the live source or from
    the nemweb archive and returns a facility interval set schema"""

    url_params = {
        "day": get_date_component("%d"),
        "month": get_date_component("%m"),
        "year": get_date_component("%Y"),
    }

    url = _AEMO_WEM_SCADA_URL

    if live:
        url = _AEMO_WEM_LIVE_SCADA_URL

    _url = url.format(**url_params)

    logger.info(f"Fetching {_url}")

    req = _wem_session.get(_url)

    if not req.ok:
        raise Exception("Get WEM facility intervals summary error: {}".format(req.status_code))

    _models = []

    csvreader = csv.DictReader(req.content.decode("utf-8").split("\n"))

    for _csv_rec in csvreader:
        # adapts the fields from balancing-summary history to match our schema
        _csv_rec = {_remap_wem_facility_interval_field(i): k for i, k in _csv_rec.items()}
        _models.append(WEMGenerationInterval(**_csv_rec))

    logger.debug(f"Got {len(_models)} facility interval records")

    wem_set = WEMFacilityIntervalSet(crawled_at=datetime.now(), live=live, intervals=_models)

    return wem_set


# debug entry point
if __name__ == "__main__":
    # m = get_wem_facility_intervals(live=False)

    m = get_wem_facility_intervals(live=True)

    with open("wem-live.json", "w") as fh:
        fh.write(m.json(indent=4))
