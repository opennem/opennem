"""
Schema definitions for the OpenNEM API v4 data endpoints.

This module contains the Pydantic models used for data endpoint responses.
"""

from datetime import datetime
from enum import Enum

from pydantic import computed_field, model_validator

from opennem.api.schema import APIV4ResponseSchema
from opennem.api.utils import get_api_network_from_code
from opennem.core.metric import get_metric_metadata
from opennem.core.time_interval import Interval
from opennem.schema.core import BaseConfig
from opennem.schema.field_types import SignificantFigures8


class DataMetric(str, Enum):
    """
    Data-specific metrics.

    These metrics are specific to facility/generation data and support
    grouping by region, fueltech, etc.
    """

    POWER = "power"
    ENERGY = "energy"
    EMISSIONS = "emissions"
    MARKET_VALUE = "market_value"
    STORAGE_BATTERY = "storage_battery"


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


class NetworkTimeSeries(BaseConfig):
    """
    Network time series data container.

    This model represents time series data for a network over a specific
    time period and interval.

    Attributes:
        network_code: The network code the data is for
        metric: The primary metric being returned (for backward compatibility)
        metrics: List of all metrics included in the response
        unit: The unit of measurement
        interval: The time interval the data is aggregated by
        start: The start time of the data range (UTC)
        end: The end time of the data range (UTC)
        groupings: List of groupings applied to the data (e.g. ["network_region", "fueltech"])
        results: List of time series results
    """

    network_code: str
    metric: DataMetric  # For backward compatibility
    unit: str = ""  # Default empty string will be replaced in validation
    interval: Interval
    start: datetime
    end: datetime
    groupings: list[str] = []
    results: list[TimeSeriesResult]

    @computed_field
    @property
    def network_timezone_offset(self) -> int:
        """
        Get the timezone offset for the network.
        """
        return get_api_network_from_code(self.network_code).get_offset_string()

    @model_validator(mode="after")
    def set_unit_from_metric(self) -> "NetworkTimeSeries":
        """Set the unit based on the primary metric if not explicitly provided."""
        if not self.unit:
            self.unit = get_metric_metadata(self.metric).unit
        return self


class NetworkTimeSeriesResponse(APIV4ResponseSchema):
    """API v4 response for network time series data."""

    data: NetworkTimeSeries | None = None
