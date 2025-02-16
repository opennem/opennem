"""
Time series schemas and response formatting for OpenNEM API.

This module contains unified schemas and response formatting logic for
time series data across both market and data endpoints.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import computed_field, model_validator

from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric, get_metric_metadata
from opennem.core.time_interval import Interval
from opennem.schema.core import BaseConfig
from opennem.schema.field_types import SignificantFigures8

# Type alias for metrics that can be either market or data metrics
type MetricType = Metric


class TimeSeriesResult(BaseConfig):
    """
    A single time series result.

    This model represents a single time series with metadata about what it represents.
    Similar to how Prometheus structures its time series results.

    Attributes:
        name: The name/identifier for this time series (e.g., "QLD1", "NSW1")
        date_start: Start time of the data range
        date_end: End time of the data range
        columns: Additional metadata as key-value pairs
        data: List of [timestamp, value] pairs
    """

    name: str
    date_start: datetime
    date_end: datetime
    columns: dict[str, str | bool] = {}
    data: list[tuple[datetime, SignificantFigures8 | None]]

    @model_validator(mode="before")
    def cast_columns_to_booleans(cls, values):
        """
        Pre-validator that converts string boolean values to actual booleans in the columns dict.
        Only processes the 'columns' field if it exists in the input values.
        """
        if "columns" in values and isinstance(values["columns"], dict):
            columns = values["columns"]
            for key, value in columns.items():
                if isinstance(value, str):
                    lower_value = value.lower()
                    if lower_value in ("true", "false"):
                        columns[key] = lower_value == "true"
        return values


class TimeSeries(BaseConfig):
    """
    Time series data container.

    This model represents time series data for a network over a specific
    time period and interval.

    Attributes:
        network_code: The network code the data is for
        metric: The metric being returned
        unit: The unit of measurement
        interval: The time interval the data is aggregated by
        start: The start time of the data range (UTC)
        end: The end time of the data range (UTC)
        groupings: List of groupings applied to the data (e.g. ["network_region", "fueltech"])
        results: List of time series results
    """

    network_code: str
    metric: MetricType
    unit: str = ""  # Default empty string will be replaced in validation
    interval: Interval
    start: datetime
    end: datetime
    groupings: list[str] = []
    results: list[TimeSeriesResult]

    @computed_field
    @property
    def network_timezone_offset(self) -> str:
        """Get the timezone offset for the network."""
        return get_api_network_from_code(self.network_code).get_offset_string()

    @model_validator(mode="after")
    def set_unit_from_metric(self) -> "TimeSeries":
        """Set the unit based on the metric if not explicitly provided."""
        if not self.unit:
            self.unit = get_metric_metadata(self.metric).unit
        return self


def format_timeseries_response(
    network: str,
    metrics: list[MetricType],
    interval: Interval,
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
    results: Sequence[dict[str, Any]],
) -> list[TimeSeries]:
    """
    Format raw query results into TimeSeries objects, one per metric.

    Args:
        network: The network code
        metrics: List of metrics queried
        interval: The time interval used
        primary_grouping: Primary grouping applied
        secondary_groupings: Secondary groupings applied (optional)
        results: Raw query results from ClickHouse as dictionaries

    Returns:
        list[TimeSeries]: List of formatted responses, one per metric
    """
    # Get min and max dates from results
    all_timestamps = [row["interval"] for row in results]
    global_date_start = min(all_timestamps)
    global_date_end = max(all_timestamps)
    dt_start = global_date_start.replace(microsecond=0)
    dt_end = global_date_end.replace(microsecond=0)

    # Combine groupings into a single list (for overall metadata)
    overall_groupings = [primary_grouping.value]
    if secondary_groupings:
        overall_groupings.extend(g.value.lower() for g in secondary_groupings)

    # Build grouping columns list based on primary and secondary grouping
    group_cols: list[str] = ["network"]
    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        group_cols.append("network_region")

    # Add secondary grouping columns if any
    if secondary_groupings:
        for grouping in secondary_groupings:
            group_cols.append(grouping.value.lower())

    # Group rows based on grouping columns
    groups: dict[str, list[dict[str, Any]]] = {}
    if group_cols:
        for row in results:
            key = tuple(str(row[col]) for col in group_cols)
            groups.setdefault(key, []).append(row)
    else:
        groups["default"] = list(results)

    # Process each metric separately
    timeseries_list = []
    for metric in metrics:
        timeseries_results = []

        for group_key, rows in groups.items():
            # Set columns and determine name prefix based on group key
            columns = {}
            name_prefix = ""
            if group_key != "default":
                columns = dict(zip(group_cols, group_key, strict=False))
                name_prefix += "_".join(str(val).lower() for val in group_key)

            # Create time series data points for this metric
            data_points: list[tuple[datetime, SignificantFigures8 | None]] = []
            for row in rows:
                timestamp = row["interval"]
                raw_value = row[metric.value.lower()]
                value = float(raw_value) if raw_value is not None else None
                data_points.append((timestamp, value))

            # Sort data points by timestamp (ascending)
            data_points.sort(key=lambda x: x[0])

            # Create time series result for this group
            series_name = f"{name_prefix}_{metric.value}".lower()
            timeseries_results.append(
                TimeSeriesResult(
                    name=series_name,
                    date_start=dt_start,
                    date_end=dt_end,
                    columns=columns,
                    data=data_points,
                )
            )

        # Create TimeSeries for this metric
        timeseries = TimeSeries(
            network_code=network,
            metric=metric,
            interval=interval,
            start=dt_start,
            end=dt_end,
            groupings=overall_groupings,
            results=timeseries_results,
        )
        timeseries_list.append(timeseries)

    return timeseries_list
