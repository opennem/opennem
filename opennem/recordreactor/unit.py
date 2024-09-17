"""
Milestone Units

This module defines Milestone Units, which are used to define the unit of measure for a milestone.
"""

from opennem.recordreactor.schema import MilestoneType, MilestoneUnitSchema

_MILESTONE_UNITS: dict[MilestoneType, MilestoneUnitSchema] = {
    MilestoneType.power: MilestoneUnitSchema(name="power", label="Power", unit="MW", output_format="{:,.0f} MW"),
    MilestoneType.energy: MilestoneUnitSchema(name="energy", label="Energy", unit="MWh", output_format="{:,.0f} MWh"),
    MilestoneType.demand: MilestoneUnitSchema(name="demand", label="Demand", unit="MW", output_format="{:,.0f} MW"),
    MilestoneType.price: MilestoneUnitSchema(name="price", label="Price", unit="AUD", output_format="{:,.2f} AUD"),
    MilestoneType.market_value: MilestoneUnitSchema(
        name="market_value", label="Market Value", unit="AUD", output_format="{:,.2f} AUD"
    ),
    MilestoneType.emissions: MilestoneUnitSchema(
        name="emissions", label="Emissions", unit="tCO2e", output_format="{:,.0f} tCO2e"
    ),
    MilestoneType.proportion: MilestoneUnitSchema(
        name="renewable_proportion", label="Renewable Proportion", unit="%", output_format="{:,.0f}%"
    ),
}


def get_milestone_unit(unit: MilestoneType) -> MilestoneUnitSchema:
    """
    Get a milestone unit by name
    """

    return _MILESTONE_UNITS[unit]


def get_milestones_units() -> list[MilestoneUnitSchema]:
    """
    Get all milestone units
    """

    return list(_MILESTONE_UNITS.values())
