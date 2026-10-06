"""Region-level forecasts into ClickHouse `market_forecast_intervals` (#675).

AEMO's rooftop PV forecast (ROOFTOP_PV FORECAST, POWERMEAN) lands here at its native 30-minute
resolution with the run time (VERSION_DATETIME) it was issued at. The table is a
ReplacingMergeTree on `version` = run time in ms, so the newest run wins for every interval and
past intervals keep the last forecast issued for them, which is what lets the API fill the
rooftop lag gap.

The crawl still writes the same forecast to `facility_scada` for the static power exports.
"""

import logging
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text

from opennem.core.normalizers import clean_float
from opennem.db import get_read_session
from opennem.db.clickhouse import execute_async, get_clickhouse_client, insert_async
from opennem.schema.network import NetworkNEM

logger = logging.getLogger("opennem.aggregates.forecast")

FORECAST_TABLE = "market_forecast_intervals"

ROOFTOP_FORECAST_METRIC = "solar_rooftop"
ROOFTOP_FORECAST_SOURCE = "ROOFTOP_PV_FORECAST"

# AEMO's file also carries sub-regions (QLDC, QLDN, TASN, ...) that would double count
_NEM_REGIONS = frozenset(NetworkNEM.regions or [])

# Backfilled rows have no known run time. Epoch ranks them below any real crawl.
_UNKNOWN_RUN_TIME = datetime(1970, 1, 1, tzinfo=UTC)

_INSERT = f"""
    INSERT INTO {FORECAST_TABLE}
    (interval, network_id, network_region, metric, source, value, run_time, horizon_minutes, version)
    VALUES
"""

type ForecastRow = tuple[datetime, str, str, str, str, float, datetime, int, int]


def _naive(value: Any) -> datetime:
    """AEMO datetimes as naive network time, parsed the same way as the facility_scada path"""
    return pd.to_datetime(value).to_pydatetime().replace(tzinfo=None)


def _forecast_row(interval: datetime, region: str, value: float, run_time: datetime, horizon_minutes: int) -> ForecastRow:
    return (
        interval,
        NetworkNEM.code,
        region,
        ROOFTOP_FORECAST_METRIC,
        ROOFTOP_FORECAST_SOURCE,
        value,
        run_time,
        horizon_minutes,
        int(run_time.timestamp() * 1000),
    )


def rooftop_forecast_rows(records: Iterable[dict[str, Any]]) -> list[ForecastRow]:
    """AEMO ROOFTOP_PV FORECAST records (lowercase keys) to `market_forecast_intervals` rows.

    Only the five NEM regions are kept. A blank POWERMEAN is no row rather than 0, so the API
    serves NULL for it.
    """
    network_tz = NetworkNEM.get_fixed_offset()
    rows: list[ForecastRow] = []

    for record in records:
        region = record.get("regionid")
        if region not in _NEM_REGIONS:
            continue

        value = record.get("powermean")
        if value is None or value == "":
            continue

        interval = _naive(record["interval_datetime"])
        run_local = _naive(record["version_datetime"])
        run_time = run_local.replace(tzinfo=network_tz).astimezone(UTC)
        horizon_minutes = max(0, int((interval - run_local).total_seconds() // 60))

        rows.append(_forecast_row(interval, region, clean_float(value), run_time, horizon_minutes))

    return rows


async def insert_forecast_rows(rows: Sequence[ForecastRow]) -> int:
    """Insert forecast rows into ClickHouse; returns the row count"""
    if not rows:
        return 0

    await insert_async(_INSERT, list(rows), timeout=60)
    return len(rows)


async def _run_already_stored(metric: str, version: int, interval_from: datetime) -> bool:
    rows = await execute_async(
        get_clickhouse_client(),
        f"SELECT count() FROM {FORECAST_TABLE} "
        "WHERE network_id = %(network)s AND metric = %(metric)s AND interval >= %(interval_from)s AND version = %(version)s",
        {"network": NetworkNEM.code, "metric": metric, "interval_from": interval_from, "version": version},
    )
    return bool(rows and rows[0][0])


async def insert_new_forecast_runs(rows: Sequence[ForecastRow]) -> int:
    """Insert each forecast run in `rows` unless that exact run is already stored.

    Guards against a crawl re-processing a file. Only an identical run is skipped: during
    catch-up an older run still holds the one interval before the next run starts, so "older
    than the newest stored" is not a duplicate.
    """
    by_run: dict[tuple[str, int], list[ForecastRow]] = {}
    for row in rows:
        by_run.setdefault((row[3], row[8]), []).append(row)

    inserted = 0
    for (metric, version), run_rows in by_run.items():
        if await _run_already_stored(metric, version, min(r[0] for r in run_rows)):
            logger.debug(f"Forecast run {metric} {version} already stored, skipping")
            continue
        inserted += await insert_forecast_rows(run_rows)

    return inserted


_PG_ROOFTOP_FORECAST = text("""
    select fs.interval, f.network_region, fs.generated
    from facility_scada fs
    join units u on u.code = fs.facility_code
    join facilities f on f.id = u.station_id
    where fs.network_id = 'AEMO_ROOFTOP'
        and fs.is_forecast is true
        and f.network_region in :regions
        and fs.interval >= :start
        and fs.interval < :end
""").bindparams(bindparam("regions", expanding=True))


async def backfill_rooftop_forecast(start: datetime, end: datetime, chunk: timedelta = timedelta(days=31)) -> int:
    """Copy facility_scada rooftop forecast history into ClickHouse.

    facility_scada keeps only the latest forecast per interval and never stored the run time,
    so these rows carry an epoch run time and version 0: any real crawl outranks them.
    """
    total = 0
    chunk_start = start

    while chunk_start < end:
        chunk_end = min(chunk_start + chunk, end)

        async with get_read_session() as session:
            result = await session.execute(
                _PG_ROOFTOP_FORECAST, {"regions": sorted(_NEM_REGIONS), "start": chunk_start, "end": chunk_end}
            )
            pg_rows = result.fetchall()

        rows = [
            _forecast_row(interval, region, float(generated), _UNKNOWN_RUN_TIME, 0)
            for interval, region, generated in pg_rows
            if generated is not None
        ]
        total += await insert_forecast_rows(rows)
        logger.info(f"Backfilled {len(rows)} rooftop forecast rows {chunk_start} -> {chunk_end}")

        chunk_start = chunk_end

    return total
