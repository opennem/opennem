"""
Core metric definitions for OpenNEM.

This module defines the different types of metrics that can be queried and
returned by the OpenNEM API. Each metric represents a different measurement
type (e.g., energy, power, emissions) and includes metadata about its
units and how it should be aggregated.
"""

from dataclasses import dataclass
from enum import Enum


class Metric(str, Enum):
    """
    Types of metrics that can be queried in OpenNEM.

    Each metric represents a different type of measurement or calculation
    that can be performed on the data.

    Attributes:
        POWER: Instantaneous power output/consumption (MW)
        ENERGY: Energy generated/consumed over time (MWh)
        PRICE: Price per unit of energy ($/MWh)
        DEMAND: Demand for energy (MW)
        CURTAILMENT_SOLAR: Curtailment of solar energy (MW)
        CURTAILMENT_WIND: Curtailment of wind energy (MW)
        MARKET_VALUE: Total market value ($)
        EMISSIONS: CO2 equivalent emissions (tonnes)
        RENEWABLE_PROPORTION: Percentage of renewable energy (%)
    """

    POWER = "power"
    ENERGY = "energy"
    PRICE = "price"
    MARKET_VALUE = "market_value"
    DEMAND = "demand"
    DEMAND_ENERGY = "demand_energy"
    CURTAILMENT_SOLAR = "curtailment_solar"
    CURTAILMENT_WIND = "curtailment_wind"
    EMISSIONS = "emissions"
    RENEWABLE_PROPORTION = "renewable_proportion"


@dataclass
class MetricMetadata:
    """
    Metadata about a metric.

    This class contains information about how a metric should be displayed
    and processed.

    Attributes:
        unit: The unit of measurement
        description: Human-readable description of the metric
        column_name: The database column name for this metric
        default_agg: The default SQL aggregation function to use
        precision: Number of decimal places to round to
    """

    unit: str
    description: str
    column_name: str
    default_agg: str
    precision: int


# Metadata for each metric type
METRIC_METADATA = {
    Metric.POWER: MetricMetadata(
        unit="MW",
        description="Power output/consumption",
        column_name="generated",
        default_agg="avg",
        precision=3,
    ),
    Metric.ENERGY: MetricMetadata(
        unit="MWh",
        description="Energy generated/consumed",
        column_name="energy",
        default_agg="sum",
        precision=3,
    ),
    Metric.PRICE: MetricMetadata(
        unit="$/MWh",
        description="Price per unit of energy",
        column_name="price",
        default_agg="avg",
        precision=2,
    ),
    Metric.MARKET_VALUE: MetricMetadata(
        unit="$",
        description="Total market value",
        column_name="market_value",
        default_agg="sum",
        precision=2,
    ),
    Metric.DEMAND: MetricMetadata(
        unit="MW",
        description="Demand generation",
        column_name="demand",
        default_agg="avg",
        precision=3,
    ),
    Metric.DEMAND_ENERGY: MetricMetadata(
        unit="MWh",
        description="Demand generation energy",
        column_name="demand_energy",
        default_agg="sum",
        precision=3,
    ),
    Metric.EMISSIONS: MetricMetadata(
        unit="t",
        description="CO2 equivalent emissions",
        column_name="emissions",
        default_agg="sum",
        precision=3,
    ),
    Metric.RENEWABLE_PROPORTION: MetricMetadata(
        unit="%",
        description="Percentage of renewable energy",
        column_name="renewable",
        default_agg="avg",
        precision=1,
    ),
    Metric.CURTAILMENT_SOLAR: MetricMetadata(
        unit="MW",
        description="Solar energy curtailment",
        column_name="curtailment_solar",
        default_agg="avg",
        precision=3,
    ),
    Metric.CURTAILMENT_WIND: MetricMetadata(
        unit="MW",
        description="Wind energy curtailment",
        column_name="curtailment_wind",
        default_agg="avg",
        precision=3,
    ),
}


def get_metric_metadata(metric: Metric) -> MetricMetadata:
    """
    Get metadata for a specific metric.

    Args:
        metric: The metric to get metadata for

    Returns:
        MetricMetadata: The metadata for the metric

    Raises:
        ValueError: If the metric is not found
    """
    if metric not in METRIC_METADATA:
        raise ValueError(f"Unknown metric: {metric}")
    return METRIC_METADATA[metric]
