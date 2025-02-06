"""
Schema definitions for the OpenNEM API v4 data endpoints.

This module contains the Pydantic models used for data endpoint responses.
"""

from datetime import datetime

from pydantic import model_validator

from opennem.api.schema import APIV4ResponseSchema
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric, get_metric_metadata
from opennem.core.time_interval import Interval
from opennem.schema.core import BaseConfig


class TimeSeriesResult(BaseConfig):
    """
    A single time series result.

    This model represents a single time series with metadata about what it represents.
    Similar to how Prometheus structures its time series results.

    Attributes:
        name: The name/identifier for this time series (e.g., "QLD1", "NSW1")
        date_start: Start time of the data range
        date_end: End time of the data range
        labels: Additional labels/tags for this series (e.g., fueltech="coal")
        data: List of [timestamp, value] pairs
    """

    name: str
    date_start: datetime
    date_end: datetime
    labels: dict[str, str] = {}
    data: list[tuple[datetime, float | None]]


class NetworkTimeSeries(BaseConfig):
    """
    Network time series data container.

    This model represents time series data for a network over a specific
    time period and interval.

    Attributes:
        network_code: The network code the data is for
        metric: The type of metric being returned
        unit: The unit of measurement
        interval: The time interval the data is aggregated by
        start: The start time of the data range (UTC)
        end: The end time of the data range (UTC)
        primary_grouping: The primary grouping type (network or network_region)
        secondary_groupings: Optional list of secondary groupings (fueltech, etc.)
        results: List of time series results
    """

    network_code: str
    metric: Metric
    unit: str = ""  # Default empty string will be replaced in validation
    interval: Interval
    start: datetime
    end: datetime
    primary_grouping: PrimaryGrouping = PrimaryGrouping.NETWORK
    secondary_groupings: list[SecondaryGrouping] = []
    results: list[TimeSeriesResult]

    @model_validator(mode="after")
    def set_unit_from_metric(self) -> "NetworkTimeSeries":
        """Set the unit based on the metric if not explicitly provided."""
        if not self.unit:
            self.unit = get_metric_metadata(self.metric).unit
        return self


class NetworkTimeSeriesResponse(APIV4ResponseSchema):
    """API v4 response for network time series data."""

    data: NetworkTimeSeries
