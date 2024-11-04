"""
Defines the OpenNEM metric schema

"""

import builtins
from decimal import Decimal
from enum import Enum

from pydantic import Field

from opennem.schema.core import BaseConfig


class MetricId(str, Enum):
    demand_mega = "demand_mega"
    demand_giga = "demand_giga"
    energy_mega = "energy_mega"
    energy_giga = "energy_giga"
    price = "price"
    market_value = "market_value"
    renewable_proportion = "renewable_proportion"


class MetricType(str, Enum):
    """The data type of the metric's values"""

    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"


class MetricSchema(BaseConfig):
    id: MetricId = Field(..., description="Metric ID ")
    name: str = Field(..., description="Human readable metric name")
    unit: str = Field(..., description="Metric unit ex. MW, MWh, AUD/MWh")
    unit_type: MetricType = Field(..., description="Metric data type")
    description: str = Field(..., description="Metric description")
    round_to: int = 2

    # should nulls in the unit series be cast
    cast_nulls: bool = True

    @property
    def python_type(self) -> builtins.type:
        """Returns the Python type for this metric"""
        return {MetricType.INTEGER: int, MetricType.FLOAT: float, MetricType.DECIMAL: Decimal}[self.unit_type]

    @property
    def value(self) -> str:
        return self.unit
