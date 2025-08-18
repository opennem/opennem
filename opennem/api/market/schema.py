"""
Market data schema definitions for OpenNEM API.

This module contains schema definitions for market data endpoints and Pydantic models for responses.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from opennem.api.utils import get_api_network_from_code


class MarketMetric(str, Enum):
    """Market metrics available in the API."""

    PRICE = "price"
    DEMAND = "demand"
    DEMAND_ENERGY = "demand_energy"
    CURTAILMENT_SOLAR = "curtailment_solar"
    CURTAILMENT_WIND = "curtailment_wind"

    @property
    def unit(self) -> str:
        """Get the unit for this metric."""
        units = {
            "price": "AUD/MWh",
            "demand": "MW",
            "demand_energy": "MWh",
            "curtailment_solar": "MW",
            "curtailment_wind": "MW",
        }
        return units[self.value]


class MarketTimeSeriesResult(BaseModel):
    """A single time series result for market data."""

    name: str = Field(description="Identifier for the series")
    date_start: datetime = Field(description="Start time of the series")
    date_end: datetime = Field(description="End time of the series")
    labels: dict[str, str] = Field(description="Additional metadata as key-value pairs")
    data: list[list[datetime | float | None]] = Field(description="List of [timestamp, value] tuples")


class MarketTimeSeries(BaseModel):
    """Time series response for market data."""

    network_code: str = Field(description="Network code")
    interval: str = Field(description="Time interval used")
    start: datetime = Field(description="Start time of the data")
    end: datetime = Field(description="End time of the data")
    results: list[MarketTimeSeriesResult] = Field(description="Time series results")

    @property
    def network_timezone_offset(self) -> str:
        """
        Get the timezone offset for the network.
        """
        return get_api_network_from_code(self.network_code).get_offset_string()

    @property
    def metric(self) -> MarketMetric:
        """
        Get the metric for this time series.
        """
        return MarketMetric(self.interval)

    @property
    def unit(self) -> str:
        """
        Get the unit for this time series.
        """
        return self.metric.unit
