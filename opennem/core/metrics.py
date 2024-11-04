"""
Defines the OpenNEM metrics
"""

from opennem.schema.metric import MetricId, MetricSchema, MetricType

METRICS = {
    MetricId.energy_mega: MetricSchema(
        id=MetricId.energy_mega,
        name="Energy (Mega)",
        unit="MWh",
        unit_type=MetricType.FLOAT,
        description="Energy in megawatt hours",
    ),
    MetricId.energy_giga: MetricSchema(
        id=MetricId.energy_giga,
        name="Energy (Giga)",
        unit="GWh",
        unit_type=MetricType.FLOAT,
        description="Energy in gigawatt hours",
    ),
    MetricId.market_value: MetricSchema(
        id=MetricId.market_value,
        name="Market Value",
        unit="AUD/MWh",
        unit_type=MetricType.FLOAT,
        description="Market value in Australian dollars per megawatt hour",
    ),
    MetricId.renewable_proportion: MetricSchema(
        id=MetricId.renewable_proportion,
        name="Renewable Proportion",
        unit="%",
        unit_type=MetricType.FLOAT,
        description="Percentage of renewable energy",
    ),
}
