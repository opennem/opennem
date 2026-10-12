import asyncio
import logging
from datetime import datetime, timedelta
from functools import partial
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache
from fastapi_versionizer import api_version
from starlette import status

from opennem.api.cache_keys import tiered_key_builder
from opennem.api.data.utils import validate_date_range
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.security import authenticated_user
from opennem.api.time import human_to_interval, human_to_period
from opennem.api.utils import get_api_network_from_code
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.core.units import get_unit
from opennem.db.clickhouse import execute_async, get_clickhouse_dependency
from opennem.schema.network import (
    NetworkSchema,
)
from opennem.utils.dates import get_last_completed_interval_for_network

from .controllers import stats_factory as _stats_factory
from .schema import DataQueryResult, OpennemDataSet

# The live API returns sparse x,y series — a missing month/year is expected and
# consumers handle the nulls — so it opts out of the static-export calendar
# gapfill that keeps file exports aligned (issue #548).
stats_factory = partial(_stats_factory, fill_monthly_gaps=False)


logger = logging.getLogger(__name__)

# Map legacy interval strings to the Interval enum
_HUMAN_TO_INTERVAL: dict[str, Interval] = {
    "5m": Interval.INTERVAL,
    "15m": Interval.INTERVAL,
    "30m": Interval.HOUR,
    "1h": Interval.HOUR,
    "1d": Interval.DAY,
    "1M": Interval.MONTH,
    "1Y": Interval.YEAR,
}


def _period_to_date_range(period_human: str, network: NetworkSchema) -> tuple[datetime, datetime]:
    """Convert a legacy period string (e.g. '7d', '1Y') to (date_start, date_end)."""
    date_end = get_last_completed_interval_for_network(network=network, tz_aware=False)

    # "all" = from the network's first data, not a fixed offset. periods.json "all" was
    # 10_512_000 min = 20y (missing a zero vs its "200 years" label), clipping deep history (#543).
    if period_human.strip() == "all" and network.data_first_seen:
        # validate_date_range wants naive network-local time
        date_start = network.data_first_seen.astimezone(network.get_fixed_offset()).replace(tzinfo=None)
        return date_start, date_end

    period_obj = human_to_period(period_human)
    date_start = date_end - timedelta(minutes=period_obj.period)
    return date_start, date_end


router = APIRouter()


# ---------------------------------------------------------------------------
# v4 station stats — ClickHouse backed, legacy format, deprecated
# ---------------------------------------------------------------------------

_DEPRECATION_MSG = "This endpoint will be removed. Use /v4/data/facilities/ instead."

# Map Interval enum → legacy TimeInterval human string
_INTERVAL_TO_HUMAN: dict[Interval, str] = {
    Interval.INTERVAL: "5m",
    Interval.HOUR: "1h",
    Interval.DAY: "1d",
    Interval.WEEK: "1w",
    Interval.MONTH: "1M",
    Interval.YEAR: "1Y",
}


@api_version(4)
@router.get(
    "/power/station/{network_code}/{facility_code:path}",
    name="Power by Station (v4, deprecated)",
    response_model=OpennemDataSet,
    response_model_exclude_unset=False,
)
@cache(expire=60 * 5, key_builder=tiered_key_builder)
async def power_station_v4(
    network_code: str,
    facility_code: str,
    period: Annotated[str, Query(description="Period e.g. 7d, 1M, 1Y")] = "7d",
    interval_human: Annotated[str | None, Query(alias="interval", description="Interval e.g. 5m, 1h, 1d")] = None,
    client: Any = Depends(get_clickhouse_dependency),
    user: authenticated_user = None,
) -> OpennemDataSet:
    """Get power output for a station. Deprecated: use /v4/data/facilities/ instead.

    .. deprecated::
        This endpoint is scheduled for removal. Migrate to
        ``GET /v4/data/facilities/{network_code}?facility_code={code}&metrics=power``.
    """
    network = get_api_network_from_code(network_code)
    date_start, date_end = _period_to_date_range(period, network)

    interval = _HUMAN_TO_INTERVAL.get(interval_human, Interval.INTERVAL) if interval_human else Interval.INTERVAL

    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    query, params, column_names = get_timeseries_query(
        query_type=QueryType.FACILITY,
        network=network,
        metrics=[Metric.POWER],
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        facility_code=[facility_code],
    )

    results = await execute_async(client, query, params)

    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data for station")

    interval_obj = human_to_interval(_INTERVAL_TO_HUMAN.get(interval, interval.value))
    units = get_unit("power")

    def _build() -> OpennemDataSet | None:
        rows = [dict(zip(column_names, row, strict=True)) for row in results]
        stats = [DataQueryResult(interval=r["interval"], group_by=r["unit_code"], result=r["power"]) for r in rows]
        return stats_factory(
            stats,
            code=facility_code,
            network=network,
            interval=interval_obj,
            include_group_code=True,
            units=units,
        )

    # row building + stats_factory is ~25 ms of CPU: keep it off the loop so cheap requests are not queued behind it
    result = await asyncio.to_thread(_build)

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No results found")

    result.messages = [_DEPRECATION_MSG]
    return result


@api_version(4)
@router.get(
    "/energy/station/{network_code}/{facility_code:path}",
    name="Energy by Station (v4, deprecated)",
    response_model=OpennemDataSet,
    response_model_exclude_unset=False,
)
@cache(expire=60 * 5, key_builder=tiered_key_builder)
async def energy_station_v4(
    network_code: str,
    facility_code: str,
    period: Annotated[str, Query(description="Period e.g. 7d, 1M, 1Y")] = "1Y",
    interval_param: Annotated[str | None, Query(alias="interval", description="Interval e.g. 1d, 1M")] = None,
    client: Any = Depends(get_clickhouse_dependency),
    user: authenticated_user = None,
) -> OpennemDataSet:
    """Get energy, emissions, and market value for a station. Deprecated: use /v4/data/facilities/ instead.

    .. deprecated::
        This endpoint is scheduled for removal. Migrate to
        ``GET /v4/data/facilities/{network_code}?facility_code={code}&metrics=energy&metrics=emissions&metrics=market_value``.
    """
    network = get_api_network_from_code(network_code)
    date_start, date_end = _period_to_date_range(period, network)

    interval = _HUMAN_TO_INTERVAL.get(interval_param, Interval.DAY) if interval_param else Interval.DAY

    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    query, params, column_names = get_timeseries_query(
        query_type=QueryType.FACILITY,
        network=network,
        metrics=[Metric.ENERGY, Metric.EMISSIONS, Metric.MARKET_VALUE],
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        facility_code=[facility_code],
    )

    results = await execute_async(client, query, params)

    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data for station")

    rows = [dict(zip(column_names, row, strict=True)) for row in results]

    interval_obj = human_to_interval(_INTERVAL_TO_HUMAN.get(interval, interval.value))

    results_energy = [DataQueryResult(interval=r["interval"], group_by=r["unit_code"], result=r["energy"]) for r in rows]
    results_emissions = [DataQueryResult(interval=r["interval"], group_by=r["unit_code"], result=r["emissions"]) for r in rows]
    results_market_value = [
        DataQueryResult(interval=r["interval"], group_by=r["unit_code"], result=r["market_value"]) for r in rows
    ]

    result = stats_factory(
        stats=results_energy,
        units=get_unit("energy"),
        network=network,
        interval=interval_obj,
        code=facility_code,
        include_group_code=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No results found")

    stats_market_value = stats_factory(
        stats=results_market_value,
        units=get_unit("market_value"),
        network=network,
        interval=interval_obj,
        code=facility_code,
        include_group_code=True,
    )
    result.append_set(stats_market_value)

    stats_emissions = stats_factory(
        stats=results_emissions,
        units=get_unit("emissions"),
        network=network,
        interval=interval_obj,
        code=facility_code,
        include_group_code=True,
    )
    result.append_set(stats_emissions)

    result.messages = [_DEPRECATION_MSG]
    return result
