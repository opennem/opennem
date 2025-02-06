"""
Core schema definitions for the OpenNEM API.

This module contains the core Pydantic models used throughout the API.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from opennem.core.time_interval import Interval


class PropertyBaseModel(BaseModel):
    """
    Workaround for serializing properties with pydantic until
    https://github.com/samuelcolvin/pydantic/issues/935
    is solved
    """

    @classmethod
    def get_properties(cls):  # type: ignore
        return [prop for prop in dir(cls) if isinstance(getattr(cls, prop), property) and prop not in ("__values__", "fields")]

    def dict(self, *args, **kwargs) -> dict:  # type: ignore
        self.__dict__.update({prop: getattr(self, prop) for prop in self.get_properties()})

        return super().dict(*args, **kwargs)


class BaseConfig(PropertyBaseModel):
    """Base configuration for all Pydantic models."""

    model_config = ConfigDict(
        from_attributes=True, str_strip_whitespace=True, arbitrary_types_allowed=True, validate_assignment=True
    )


class EnergyDataPoint(BaseConfig):
    """
    A single data point in the energy time series.

    This model represents energy data for a specific fuel tech group at a
    specific point in time.

    Attributes:
        interval: The timestamp for this data point
        fueltech_group: The fuel tech group code
        energy: Energy in MWh
        emissions: CO2 emissions in tonnes
        market_value: Market value in AUD
    """

    interval: datetime
    fueltech_group: str
    energy: float | None = Field(default=None, description="Energy in MWh")
    emissions: float | None = Field(default=None, description="CO2 emissions in tonnes")
    market_value: float | None = Field(default=None, description="Market value in AUD")


class NetworkEnergyResponse(BaseConfig):
    """
    Response model for network energy data.

    This model represents aggregated energy data for a network over a specific
    time period and interval.

    Attributes:
        network_code: The network code the data is for
        interval: The time interval the data is aggregated by
        start: The start time of the data range (UTC)
        end: The end time of the data range (UTC)
        data: List of energy data points
    """

    network_code: str
    interval: Interval
    start: datetime
    end: datetime
    data: list[EnergyDataPoint]
