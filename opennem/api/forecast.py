"""Forecast metrics on the v4 market endpoint (#675).

Forecasts live in ClickHouse `market_forecast_intervals`, one row per (network, metric, region,
interval) at the source's native 30-minute resolution, newest run winning. Every query expands
each row onto the 5-minute grid first (a row labelled T covers T to T+25m, the same step fill as
the actual rooftop series in unit_intervals, #579) and then buckets, so any interval and any
off-grid window average the same steps the 5m series shows.

The query returns the same column shape as `get_timeseries_query`, so the results go through the
usual `format_timeseries_response`.
"""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from opennem.core.grouping import PrimaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval, get_interval_function
from opennem.db.clickhouse import execute_async
from opennem.schema.network import NetworkSchema

FORECAST_TABLE = "market_forecast_intervals"

# API metric -> `metric` key in the forecast table
FORECAST_METRICS: dict[Metric, str] = {
    Metric.SOLAR_ROOFTOP_FORECAST: "solar_rooftop",
}

# Forecast sources publish on a 30-minute grid; each row fills six 5-minute steps.
SOURCE_INTERVAL = timedelta(minutes=30)
_STEP_OFFSETS = (0, 5, 10, 15, 20, 25)


def is_forecast_metric(metric: Metric) -> bool:
    return metric in FORECAST_METRICS


def _base_filters(
    network: NetworkSchema, metrics: Sequence[Metric], network_region: str | None
) -> tuple[list[str], dict[str, Any]]:
    params: dict[str, Any] = {
        "network": tuple(network.get_network_codes()),
        "metrics": tuple(FORECAST_METRICS[m] for m in metrics),
    }
    filters = ["network_id IN %(network)s", "metric IN %(metrics)s"]
    if network_region:
        filters.append("network_region = %(network_region)s")
        params["network_region"] = network_region
    return filters, params


def get_forecast_timeseries_query(
    network: NetworkSchema,
    metrics: Sequence[Metric],
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
    primary_grouping: PrimaryGrouping = PrimaryGrouping.NETWORK,
    network_region: str | None = None,
) -> tuple[str, dict[str, Any], list[str]]:
    """Build the forecast time-series query over [date_start, date_end).

    A network-level total is NULL at any 5-minute step where a region is missing, never a
    partial sum.
    """
    unknown = [m for m in metrics if m not in FORECAST_METRICS]
    if unknown:
        raise ValueError(f"Not forecast metrics: {', '.join(m.value for m in unknown)}")

    filters, params = _base_filters(network, metrics, network_region)

    by_region = primary_grouping == PrimaryGrouping.NETWORK_REGION
    regions_required = 1 if (by_region or network_region) else len(network.regions or [])

    # the row covering date_start starts up to 25 minutes before it
    params["source_start"] = (date_start - SOURCE_INTERVAL + timedelta(minutes=5)).replace(tzinfo=None)
    params["date_start"] = date_start.replace(tzinfo=None)
    params["date_end"] = date_end.replace(tzinfo=None)
    params["regions_required"] = max(regions_required, 1)

    region_col = ["network_region"] if by_region else []

    inner_metrics: list[str] = []
    outer_metrics: list[str] = []
    for m in metrics:
        key = FORECAST_METRICS[m]
        inner_metrics.append(f"sumIf(value, metric = '{key}') AS {key}_sum")
        # FINAL makes (network, metric, region, interval) unique, so the row count is the region count
        inner_metrics.append(f"countIf(metric = '{key}') AS {key}_regions")
        outer_metrics.append(f"round(avg(if({key}_regions >= %(regions_required)s, {key}_sum, NULL)), 6) AS {m.value}")

    bucket_fn = get_interval_function(interval, "raw_interval", database="clickhouse")
    group_inner = ", ".join(["raw_interval", *region_col])
    group_outer = ", ".join(["interval", *region_col])
    offsets = ", ".join(str(o) for o in _STEP_OFFSETS)

    sql = f"""
    WITH expanded AS (
        SELECT
            interval + toIntervalMinute(step) AS raw_interval,
            network_region,
            metric,
            value
        FROM {FORECAST_TABLE} FINAL
        ARRAY JOIN [{offsets}] AS step
        WHERE {" AND ".join([*filters, "interval >= %(source_start)s", "interval < %(date_end)s"])}
    ),
    inner_agg AS (
        SELECT
            {", ".join(["raw_interval", *region_col, *inner_metrics])}
        FROM expanded
        WHERE raw_interval >= %(date_start)s AND raw_interval < %(date_end)s
        GROUP BY {group_inner}
    )
    SELECT
        {bucket_fn} AS interval,
        {", ".join([f"'{network.code}' AS network", *region_col, *outer_metrics])}
    FROM inner_agg
    GROUP BY {group_outer}
    ORDER BY {", ".join(["interval DESC", *region_col])}
    """

    column_names = ["interval", "network", *region_col, *(m.value for m in metrics)]
    return sql, params, column_names


async def get_latest_forecast_interval(client: Any, network: NetworkSchema, metrics: Sequence[Metric]) -> datetime | None:
    """Last interval any requested forecast covers (naive network time), or None when there are none"""
    filters, params = _base_filters(network, metrics, None)
    rows = await execute_async(
        client,
        f"SELECT max(interval) FROM {FORECAST_TABLE} WHERE {' AND '.join(filters)} AND interval >= now() - INTERVAL 3 DAY",
        params,
    )
    latest = rows[0][0] if rows else None
    if latest is None or latest.year < 2000:
        return None
    return latest.replace(tzinfo=None)


async def get_forecast_run_times(
    client: Any,
    network: NetworkSchema,
    metrics: Sequence[Metric],
    date_start: datetime,
    date_end: datetime,
    network_region: str | None = None,
) -> dict[Metric, datetime]:
    """Newest run time (UTC) behind each metric's values in the window.

    Backfilled rows carry an epoch run time; a window with only those has no run time.
    """
    filters, params = _base_filters(network, metrics, network_region)
    params["source_start"] = (date_start - SOURCE_INTERVAL + timedelta(minutes=5)).replace(tzinfo=None)
    params["date_end"] = date_end.replace(tzinfo=None)
    rows = await execute_async(
        client,
        f"SELECT metric, max(run_time) FROM {FORECAST_TABLE} FINAL "
        f"WHERE {' AND '.join([*filters, 'interval >= %(source_start)s', 'interval < %(date_end)s'])} "
        "GROUP BY metric",
        params,
    )
    by_key = {key: metric for metric, key in FORECAST_METRICS.items()}
    run_times: dict[Metric, datetime] = {}
    for key, run_time in rows or []:
        if key not in by_key or run_time is None:
            continue
        run_time = run_time if run_time.tzinfo else run_time.replace(tzinfo=UTC)
        if run_time.year < 2000:
            continue
        run_times[by_key[key]] = run_time
    return run_times
