"""
Time series schemas and response formatting for OpenNEM API.

This module contains unified schemas and response formatting logic for
time series data across both market and data endpoints.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import ConfigDict, computed_field, model_validator

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
    columns: dict[str, str | bool | int | list[float] | list[int]] = {}
    data: list[tuple[datetime, SignificantFigures8 | None]]

    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    # @model_validator(mode="after")
    def add_network_timezone(self) -> Any:
        """Add network timezone to all datetime fields based on parent TimeSeries network."""
        # Get parent context which should contain network_code
        context = self.model_config.get("context", {})
        network_code = context.get("network_code")

        if network_code:
            network = get_api_network_from_code(network_code)
            tz_offset = network.get_fixed_offset()

            # Apply timezone to all datetime values in data
            if self.data:
                self.data = [
                    (timestamp.replace(tzinfo=tz_offset), value) if timestamp and not timestamp.tzinfo else (timestamp, value)
                    for timestamp, value in self.data
                ]

        return self


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
    date_start: datetime
    date_end: datetime
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

    @model_validator(mode="after")
    def add_network_to_results(self) -> "TimeSeries":
        """Add network_code to results context for timezone conversion."""
        # Create context with network_code for results
        context = {"network_code": self.network_code}

        # Update each result's context with the network_code
        for result in self.results:
            result.model_config["context"] = context

        return self


def format_timeseries_response(
    network: str,
    metrics: list[MetricType],
    interval: Interval,
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
    results: Sequence[dict[str, Any]],
    facility_code: str | None = None,
) -> list[TimeSeries]:
    """
    Format time series query results into the API response format.

    Args:
        network: Network code
        metrics: List of metrics that were queried
        interval: Time interval used
        primary_grouping: Primary grouping that was applied
        secondary_groupings: Optional sequence of secondary groupings that were applied
        results: Query results as sequence of dictionaries
        facility_code: Optional facility code for facility-level queries

    Returns:
        list[TimeSeries]: List of time series objects, one per metric
    """
    # Get network timezone
    network_obj = get_api_network_from_code(network)
    tz_offset = network_obj.get_fixed_offset()

    # Initialize response objects for each metric
    timeseries_list = []

    for metric in metrics:
        metric_name = metric.value.lower()

        # Group results by the grouping dimensions
        grouped_results = {}

        for row in results:
            # Apply timezone to interval
            if isinstance(row["interval"], datetime):
                row["interval"] = row["interval"].replace(tzinfo=tz_offset)

            # Build label key based on groupings
            label_parts = []

            if facility_code:
                # For facility queries, group by unit_code
                label_key = str(row["unit_code"])
                labels = {"unit_code": str(row["unit_code"])}
            else:
                # For network queries, use primary and secondary groupings
                if primary_grouping == PrimaryGrouping.NETWORK_REGION:
                    label_parts.append(row["network_region"])

                if secondary_groupings:
                    for grouping in secondary_groupings:
                        if grouping == SecondaryGrouping.RENEWABLE:
                            label_parts.append(str(row["renewable"]))
                        elif grouping == SecondaryGrouping.FUELTECH:
                            label_parts.append(row["fueltech"])
                        elif grouping == SecondaryGrouping.FUELTECH_GROUP:
                            label_parts.append(row["fueltech_group"])

                label_key = "|".join(label_parts) if label_parts else "total"

                # Build labels dictionary
                labels = {}
                if primary_grouping == PrimaryGrouping.NETWORK_REGION:
                    labels["region"] = row["network_region"]
                if secondary_groupings:
                    for grouping in secondary_groupings:
                        if grouping == SecondaryGrouping.RENEWABLE:
                            labels["renewable"] = row["renewable"]
                        elif grouping == SecondaryGrouping.FUELTECH:
                            labels["fueltech"] = row["fueltech"]
                        elif grouping == SecondaryGrouping.FUELTECH_GROUP:
                            labels["fueltech_group"] = row["fueltech_group"]

            # Initialize group if not exists
            if label_key not in grouped_results:
                grouped_results[label_key] = {
                    "name": f"{metric_name}_{label_key}",
                    "network": network,
                    "interval": interval.value,
                    "data": [],
                    "labels": labels,
                }
                if facility_code:
                    grouped_results[label_key]["facility_code"] = facility_code

            # Add data point with timezone-aware timestamp
            # Handle None values gracefully - skip them or use None
            metric_value = None
            if metric_name in row and row[metric_name] is not None:
                metric_value = float(row[metric_name])
            else:
                # Debug missing metric
                if metric_name not in row:
                    import logging

                    logger = logging.getLogger("opennem.api.timeseries")
                    logger.warning(f"Metric '{metric_name}' not found in row. Available keys: {list(row.keys())}")
                    logger.debug(f"Full row data: {row}")

            if isinstance(row["interval"], datetime):
                grouped_results[label_key]["data"].append([row["interval"].timestamp() * 1000, metric_value])
            else:
                grouped_results[label_key]["data"].append([row["interval"], metric_value])

        # Sort data points by timestamp and filter out None values if needed
        for group in grouped_results.values():
            # Convert timestamps - keep all data points including None values
            converted_data = []
            for timestamp, value in group["data"]:
                # For storage_battery metric, None values are valid (no change in storage)
                # For other metrics, we may want to skip None values
                converted_timestamp = (
                    datetime.fromtimestamp(timestamp / 1000, tz=tz_offset)
                    if isinstance(timestamp, float)
                    else datetime.combine(timestamp, datetime.min.time(), tzinfo=tz_offset)
                )
                converted_data.append((converted_timestamp, value))

            group["data"] = converted_data
            group["data"].sort(key=lambda x: x[0])

        # Filter out groups that have no data at all
        # But keep groups with data even if all values are None (valid for some metrics)
        grouped_results = {k: v for k, v in grouped_results.items() if v["data"]}

        # Skip this metric entirely if no data exists
        if not grouped_results:
            import logging

            logger = logging.getLogger("opennem.api.timeseries")
            logger.warning(f"No grouped results for metric {metric_name}")
            continue

        # Get timezone-aware start and end dates from actual data (not from query)
        all_timestamps = []
        for group in grouped_results.values():
            all_timestamps.extend([timestamp for timestamp, _ in group["data"]])

        if all_timestamps:
            date_start = min(all_timestamps)
            date_end = max(all_timestamps)
        else:
            # Fall back to original dates if no valid data
            date_start = min(row["interval"] for row in results)
            date_end = max(row["interval"] for row in results)

        # Create TimeSeries for this metric
        timeseries = TimeSeries(
            network_code=network,
            metric=metric,
            interval=interval,
            date_start=date_start,  # Already timezone-aware
            date_end=date_end,  # Already timezone-aware
            groupings=[primary_grouping.value] + [g.value.lower() for g in secondary_groupings] if secondary_groupings else [],
            results=[
                TimeSeriesResult(
                    name=group["name"],
                    date_start=date_start,  # Already timezone-aware
                    date_end=date_end,  # Already timezone-aware
                    columns=group["labels"],
                    data=group["data"],
                )
                for group in grouped_results.values()
            ],
        )
        timeseries_list.append(timeseries)

        # Debug the actual timeseries object
        import logging

        logger = logging.getLogger("opennem.api.timeseries")
        logger.debug(f"TimeSeries for {metric_name}: {len(timeseries.results)} results")
        if timeseries.results:
            logger.debug(f"First result: name={timeseries.results[0].name}, data_points={len(timeseries.results[0].data)}")
            if timeseries.results[0].data:
                logger.debug(f"Sample data point: {timeseries.results[0].data[0]}")

    return timeseries_list
