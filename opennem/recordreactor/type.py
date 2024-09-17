"""
This module defines MilestoneTypes, which are used to group milestone records into
a single type used to determine the query and aggregation logic.
"""

from opennem.recordreactor.schema import MilestonePeriod, MilestoneType, MilestoneTypeSchema

_MILESTONE_TYPES: dict[MilestoneType, MilestoneTypeSchema] = {
    MilestoneType.demand: MilestoneTypeSchema(
        name="demand",
        label="Demand",
        unit="MW",
        description="The total demand for electricity in the system",
        significance_weight=1.0,
        periods=[
            MilestonePeriod.interval,
            MilestonePeriod.day,
            MilestonePeriod.week_rolling,
            MilestonePeriod.month,
            MilestonePeriod.quarter,
            MilestonePeriod.year,
            MilestonePeriod.financial_year,
        ],
    )
}


def get_milestone_type_by_name(name: str) -> MilestoneTypeSchema:
    """
    Get a milestone type by name
    """

    return _MILESTONE_TYPES[MilestoneType(name)]


def get_milestone_type(type: MilestoneType) -> MilestoneTypeSchema:
    """
    Get a milestone type by name
    """

    return _MILESTONE_TYPES[type]
