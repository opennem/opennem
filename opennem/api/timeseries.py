"""
Time series schemas and response formatting for OpenNEM API.

This module contains unified schemas and response formatting logic for
time series data across both market and data endpoints.
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import ConfigDict, computed_field, model_validator

from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric, get_metric_metadata
from opennem.core.time_interval import Interval
from opennem.schema.core import BaseConfig
from opennem.utils.dates import get_today_opennem
from opennem.utils.version import get_version

logger = logging.getLogger("opennem.api.timeseries")


# ---------------------------------------------------------------------------
# Pydantic models — kept for backward compat (used by pollution router).
# The hot-path data/market endpoints bypass these via format_timeseries_response().
# ---------------------------------------------------------------------------


class TimeSeriesResult(BaseConfig):
    """A single time series result (Pydantic model for non-hot-path endpoints)."""

    name: str
    date_start: datetime
    date_end: datetime
    columns: dict[str, str | bool | int | list[float] | list[int]] = {}
    data: list[tuple[datetime, float | None]]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="before")
    def cast_columns_to_booleans(cls, values):
        if "columns" in values and isinstance(values["columns"], dict):
            columns = values["columns"]
            for key, value in columns.items():
                if isinstance(value, str):
                    lower_value = value.lower()
                    if lower_value in ("true", "false"):
                        columns[key] = lower_value == "true"
        return values


class TimeSeries(BaseConfig):
    """Time series data container (Pydantic model for non-hot-path endpoints)."""

    network_code: str
    metric: Metric
    unit: str = ""
    interval: Interval
    date_start: datetime
    date_end: datetime
    groupings: list[str] = []
    results: list[TimeSeriesResult]

    @computed_field
    @property
    def network_timezone_offset(self) -> str:
        return get_api_network_from_code(self.network_code).get_offset_string()

    @model_validator(mode="after")
    def set_unit_from_metric(self) -> "TimeSeries":
        if not self.unit:
            self.unit = get_metric_metadata(self.metric).unit
        return self


# Type alias for metrics that can be either market or data metrics
type MetricType = Metric

# Grouping enum value → row dict key
_GROUPING_COL = {
    SecondaryGrouping.RENEWABLE: "renewable",
    SecondaryGrouping.FUELTECH: "fueltech",
    SecondaryGrouping.FUELTECH_GROUP: "fueltech_group",
}

# Grouping enum value → labels dict key (same for most, but explicit)
_GROUPING_LABEL = {
    SecondaryGrouping.RENEWABLE: "renewable",
    SecondaryGrouping.FUELTECH: "fueltech",
    SecondaryGrouping.FUELTECH_GROUP: "fueltech_group",
}


def _build_label_key_and_labels(
    row: dict[str, Any],
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
    facility_code: str | list[str] | None,
) -> tuple[str, dict[str, Any]]:
    """Build the group key string and labels dict for a row."""
    if facility_code:
        key = str(row["unit_code"])
        return key, {"unit_code": key}

    parts: list[str] = []
    labels: dict[str, Any] = {}

    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        parts.append(row["network_region"])
        labels["region"] = row["network_region"]

    if secondary_groupings:
        for g in secondary_groupings:
            col = _GROUPING_COL[g]
            parts.append(str(row[col]))
            labels[_GROUPING_LABEL[g]] = row[col]

    return ("|".join(parts) if parts else "total"), labels


def format_timeseries_response(
    network: str,
    metrics: list[MetricType],
    interval: Interval,
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
    results: Sequence[dict[str, Any]],
    facility_code: str | None = None,
) -> list[dict[str, Any]]:
    """
    Format time series query results into plain dicts ready for orjson serialization.

    Returns list of TimeSeries-shaped dicts, one per metric.
    """
    network_obj = get_api_network_from_code(network)
    tz_offset = network_obj.get_fixed_offset()
    tz_offset_str = network_obj.get_offset_string()

    # Pre-convert all interval values to tz-aware datetimes once
    for row in results:
        iv = row["interval"]
        if isinstance(iv, datetime):
            row["interval"] = iv.replace(tzinfo=tz_offset)
        else:
            row["interval"] = datetime.combine(iv, datetime.min.time(), tzinfo=tz_offset)

    timeseries_list: list[dict[str, Any]] = []

    for metric in metrics:
        metric_name = metric.value.lower()
        meta = get_metric_metadata(metric)

        # --- group rows ---
        grouped: dict[str, dict[str, Any]] = {}

        for row in results:
            label_key, labels = _build_label_key_and_labels(row, primary_grouping, secondary_groupings, facility_code)

            if label_key not in grouped:
                grouped[label_key] = {
                    "name": f"{metric_name}_{label_key}",
                    "columns": labels,
                    "data": [],
                }

            value = None
            if metric_name in row and row[metric_name] is not None:
                value = float(row[metric_name])
            elif metric_name not in row:
                logger.warning(f"Metric '{metric_name}' not in row. Keys: {list(row.keys())}")

            grouped[label_key]["data"].append((row["interval"], value))

        # sort + filter empty
        for g in grouped.values():
            g["data"].sort(key=lambda x: x[0])

        grouped = {k: v for k, v in grouped.items() if v["data"]}

        if not grouped:
            logger.warning(f"No grouped results for metric {metric_name}")
            continue

        # date range from actual data
        all_ts = [ts for g in grouped.values() for ts, _ in g["data"]]
        date_start = min(all_ts)
        date_end = max(all_ts)

        # build groupings list
        groupings: list[str] = []
        if secondary_groupings:
            groupings = [primary_grouping.value] + [g.value.lower() for g in secondary_groupings]

        # build result dicts (no Pydantic)
        result_dicts = []
        for g in grouped.values():
            # convert (datetime, value) tuples to [iso_string, value] for JSON
            data_out = [[ts.isoformat(), v] for ts, v in g["data"]]
            result_dicts.append(
                {
                    "name": g["name"],
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "columns": g["columns"],
                    "data": data_out,
                }
            )

        timeseries_list.append(
            {
                "network_code": network,
                "metric": metric_name,
                "unit": meta.unit,
                "interval": interval.value,
                "date_start": date_start.isoformat(),
                "date_end": date_end.isoformat(),
                "groupings": groupings,
                "results": result_dicts,
                "network_timezone_offset": tz_offset_str,
            }
        )

    return timeseries_list


def build_timeseries_response(timeseries_list: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build a plain dict payload for the API response.
    Returned directly from FastAPI endpoints — avoids Pydantic
    serialization while remaining compatible with @cache.
    """
    return {
        "version": get_version(),
        "created_at": get_today_opennem().isoformat(),
        "success": True,
        "data": timeseries_list,
    }
