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
from collections import Counter
from datetime import datetime, timedelta
from io import StringIO
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from opennem.schema.network import NetworkWEM
from opennem.utils.dates import get_date_component, parse_date
from opennem.utils.http import http

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

# WEM published 30-minute trading intervals for the whole life of the legacy
# facility-scada archive (2006-09 through the WEMDE cutover on 2023-10-01).
# WEMDE dispatch intervals are 5-minute and are handled by opennem.clients.wemde.
WEM_LEGACY_INTERVAL_SIZE_MINUTES = 30

# Cadences WEM has actually published: 30 minute legacy trading intervals and 5 minute
# WEMDE dispatch intervals. Anything else is treated as a detection failure.
WEM_VALID_INTERVAL_SIZES = (5, 30)

# The date AEMO began publishing the "EOI Quantity (MW)" column in the facility-scada
# archive. Records before this carry only "Energy Generated (MWh)". See #598.
WEM_EOI_QUANTITY_FIRST_SEEN = datetime(2013, 12, 17)

# Create aiohttp session


def _wem_balancing_summary_field_alias(field_name: str) -> str:
    """Generates field aliases to map balancing summary CSV to schema"""
    return field_name.strip().upper()


def _empty_string_to_none(field_value: str | float | None) -> float | None:
    """Convert empty strings to None and strings to floats.

    Runs as a BeforeValidator: AEMO leaves numeric columns as empty strings rather than
    omitting them (the whole "EOI Quantity (MW)" column is empty before 2013-12-17), and
    pydantic's own float coercion rejects "" before an AfterValidator would ever see it.

    A published zero is preserved as 0.0 — it means the unit ran at zero, which is real
    data and distinct from a missing value.
    """
    if field_value is None:
        return None

    if isinstance(field_value, str):
        field_value = field_value.strip()

        if not field_value:
            return None

        try:
            return float(field_value)
        except ValueError:
            return None

    return float(field_value)


FloatField = Annotated[float | None, BeforeValidator(_empty_string_to_none)]


class WEMBalancingSummaryInterval(BaseModel):
    trading_day_interval: datetime
    forecast_eoi_mw: FloatField = None
    forecast_mw: FloatField = None
    price: FloatField = None
    forecast_nsg_mw: FloatField = None
    actual_nsg_mw: FloatField = None
    actual_total_generation: FloatField = None

    @field_validator("trading_day_interval", mode="before")
    @classmethod
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(value, network=NetworkWEM)

        if not interval_time:
            raise ValueError(f"Invalid APVI forecast interval: {value}")

        return interval_time

    @property
    def is_forecast(self) -> bool:
        # `is None`, not falsiness: a published zero is an actual reading, not a missing
        # one, and zeros are now preserved rather than coerced to None
        return self.actual_total_generation is None and self.actual_nsg_mw is None

    model_config = ConfigDict(alias_generator=_wem_balancing_summary_field_alias)


class WEMBalancingSummarySet(BaseModel):
    crawled_at: datetime
    live: bool = True
    intervals: list[WEMBalancingSummaryInterval]
    source_url: str | None = None
    server_latest: datetime | None = None

    @property
    def count(self) -> int:
        return len(self.intervals)


class WEMGenerationInterval(BaseModel):
    trading_interval: datetime
    network_id: str = "WEM"
    facility_code: str
    power: FloatField = None
    eoi_quantity: FloatField = None
    generated_scheduled: FloatField = None
    generated_non_scheduled: FloatField = None

    # Length of the interval this record covers, in minutes. WEM published 30-minute
    # trading intervals until the WEMDE cutover (2023-10-01), after which dispatch is
    # 5-minute. Used to convert between energy (MWh/interval) and power (MW).
    interval_size_minutes: int = WEM_LEGACY_INTERVAL_SIZE_MINUTES

    created_by: str = "controllers.wem"
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def intervals_per_hour(self) -> float:
        return 60 / self.interval_size_minutes

    @property
    def generated(self) -> float | None:
        """Generation in MW.

        AEMO only began publishing the `EOI Quantity (MW)` column on 2013-12-17; before
        that the archive carries `Energy Generated (MWh)` alone. Derive power from energy
        in that era rather than returning null (see #598).
        """
        if self.power is not None:
            return self.power

        if self.generated_scheduled is not None and self.generated_non_scheduled is not None:
            return self.generated_scheduled + self.generated_non_scheduled

        if self.generated_non_scheduled is not None:
            return self.generated_non_scheduled

        if self.generated_scheduled is not None:
            return self.generated_scheduled

        if self.eoi_quantity is not None:
            return self.eoi_quantity * self.intervals_per_hour

        return None

    @property
    def energy(self) -> float | None:
        """Energy in MWh for the interval.

        Mirrors the WEMDE client, which stores the published MWh quantity as-is and
        derives `generated` from it.
        """
        if self.eoi_quantity is not None:
            return self.eoi_quantity

        if self.power is not None:
            return self.power / self.intervals_per_hour

        return None

    @field_validator("trading_interval", mode="before")
    @classmethod
    def _validate_trading_interval(cls, value: Any) -> datetime:
        interval_time = parse_date(value, network=NetworkWEM)

        if not interval_time:
            raise ValueError(f"Invalid APVI forecast interval: {value}")

        return interval_time


class WEMFacilityIntervalSet(BaseModel):
    crawled_at: datetime
    live: bool = True
    intervals: list[WEMGenerationInterval]
    source_url: str | None = None
    server_latest: datetime | None = None

    @property
    def count(self) -> int:
        return len(self.intervals)


class WEMFileNotFoundException(Exception):
    pass


async def wem_downloader(url: str, for_date: datetime | None = None) -> str:
    """Downloads WEM content using the session"""
    url_params = {
        "day": get_date_component("%d", dt=for_date),
        "month": get_date_component("%m", dt=for_date),
        "year": get_date_component("%Y", dt=for_date),
    }

    _url_parsed = url.format(**url_params)

    logger.info(f"Fetching {_url_parsed}")

    response = await http.get(_url_parsed)

    # sometimes with the WEM delay the current
    # month isn't up
    if response.status_code == 404:
        raise WEMFileNotFoundException()

    if not response.is_success:
        raise Exception(f"Get WEM facility intervals summary error: {response.status_code}")

    # @TODO mime detect and decoding
    return response.text


def _parse_csv_record(record: dict[str, str], model_class: type[BaseModel]) -> BaseModel | None:
    """Parse a CSV record into a Pydantic model with proper type coercion"""
    try:
        return model_class.model_validate(record)
    except ValidationError as e:
        logger.error(f"Validation error for record: {e}")
        logger.debug(record)
        return None


def parse_wem_live_balancing_summary(content: str) -> list[WEMBalancingSummaryInterval]:
    """Parses a WEM live balancing summary response into models"""
    _models = []
    csvreader = csv.DictReader(content.split("\n"))

    logger.debug("CSV has fields: {}".format(", ".join(csvreader.fieldnames)))  # type: ignore

    for _csv_rec in csvreader:
        model = _parse_csv_record(_csv_rec, WEMBalancingSummaryInterval)
        if model:
            _models.append(model)

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

        model = _parse_csv_record(_csv_rec, WEMBalancingSummaryInterval)
        if model:
            _models.append(model)

    logger.debug(f"Got {len(_models)} balancing summary records")

    return _models


async def get_wem_live_balancing_summary() -> WEMBalancingSummarySet:
    """Obtains WEM live balancing summary from pulse with forecasts
    (price, generation etc.) and returns a summary set model"""
    resp = await wem_downloader(_AEMO_WEM_LIVE_BALANCING_URL)

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


async def get_wem_balancing_summary() -> WEMBalancingSummarySet:
    """Obtains WEM balancing summary (price, generation etc.) and returns a
    summary set model"""
    resp = await wem_downloader(_AEMO_WEM_BALANCING_SUMMARY_URL)

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


def _detect_interval_size_minutes(intervals: list[datetime]) -> int:
    """Infer the interval size of a WEM dataset from its distinct timestamps.

    The legacy archive is 30-minute for its whole life and the WEMDE-era feeds are
    5-minute, but detecting rather than assuming keeps energy/power conversion correct
    if AEMO changes cadence again.

    Uses the most common gap rather than the smallest: a single malformed or duplicated
    timestamp would drag a minimum down and silently apply the wrong MWh->MW factor to
    every record in the file. Falls back to the legacy size if the dominant gap is not a
    cadence WEM has ever published.
    """
    distinct = sorted(set(intervals))

    if len(distinct) < 2:
        return WEM_LEGACY_INTERVAL_SIZE_MINUTES

    deltas = [int((b - a).total_seconds() // 60) for a, b in zip(distinct, distinct[1:], strict=False)]
    deltas = [d for d in deltas if d > 0]

    if not deltas:
        return WEM_LEGACY_INTERVAL_SIZE_MINUTES

    dominant = Counter(deltas).most_common(1)[0][0]

    if dominant not in WEM_VALID_INTERVAL_SIZES:
        logger.warning(f"Unexpected WEM interval size {dominant}min, falling back to {WEM_LEGACY_INTERVAL_SIZE_MINUTES}min")
        return WEM_LEGACY_INTERVAL_SIZE_MINUTES

    return dominant


def parse_wem_facility_intervals(content: str, interval_size_minutes: int | None = None) -> list[WEMGenerationInterval]:
    """parses the wem live generation intervals for each facility

    Args:
        interval_size_minutes: Override the interval size. When not given it is detected
            from the distinct trading intervals in the payload.
    """

    _models = []

    csvreader = csv.DictReader(content.split("\n"))

    _records = []

    for _csv_rec in csvreader:
        # adapts the fields from balancing-summary history to match our schema
        _records.append({_remap_wem_facility_interval_field(i): k for i, k in _csv_rec.items()})

    for _csv_rec in _records:
        model = _parse_csv_record(_csv_rec, WEMGenerationInterval)
        if model:
            _models.append(model)

    if interval_size_minutes is None:
        interval_size_minutes = _detect_interval_size_minutes([i.trading_interval for i in _models])

    for model in _models:
        model.interval_size_minutes = interval_size_minutes

    logger.debug(f"Got {len(_models)} facility interval records at {interval_size_minutes}min intervals")

    return _models


async def get_wem_live_facility_intervals(
    trim_intervals: bool = False, from_interval: datetime | None = None
) -> WEMFacilityIntervalSet:
    """Obtains WEM live facility intervals from infogrphic feeds"""
    content = await wem_downloader(_AEMO_WEM_LIVE_SCADA_URL)
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


async def get_wem_facility_intervals(
    from_date: datetime | None = None, fallback_to_recent: bool = True
) -> WEMFacilityIntervalSet:
    """Obtains WEM facility intervals from NEM web. Will default to most recent date

    Args:
        fallback_to_recent: When the requested month is missing, fall back to the file from
            30 days ago. Useful for the live crawler where the current month may not be up
            yet, but wrong for a historical backfill - a missing month must surface as
            WEMFileNotFoundException so the caller can skip it, not silently return a
            different month's data.

    @TODO not yet smart enough to know if it should check current or archive
    """
    content: str | None = None

    try:
        content = await wem_downloader(_AEMO_WEM_SCADA_URL, from_date)
    except WEMFileNotFoundException:
        if not fallback_to_recent:
            raise

        _now = datetime.now()
        from_date = _now - timedelta(days=30)
        content = await wem_downloader(_AEMO_WEM_SCADA_URL, from_date)

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


async def get_wem2_live_generation_models() -> list[WEMGenerationInterval]:
    """Gets the latest WEM live generation CSV"""
    resp = await wem_downloader(_AEMO_WEM2_GENERATION_URL)

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
                raise ValueError(f"Invalid AS_AT date: {facility_record['AS_AT']}")

        if not latest_interval:
            raise ValueError("No latest interval found")

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


async def get_wem2_live_facility_intervals(
    trim_intervals: bool = False, from_interval: datetime | None = None
) -> WEMFacilityIntervalSet:
    """Obtains WEM v2 live facility intervals from infogrphic feeds"""
    _models = await get_wem2_live_generation_models()

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
    import asyncio

    async def main():
        balancing_set = await get_wem_live_balancing_summary()
        for model in balancing_set.intervals:
            print(dict(model))

    asyncio.run(main())
