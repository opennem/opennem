"""
Filters out irrelevant data

* For each interval do generation
* For every other bucket (day, week, month, year) do energy
* lowest
"""

from opennem.recordreactor.schema import MilestoneRecordSchema


def record_is_filtered(record: MilestoneRecordSchema, filter: list[str]) -> bool:
    """Check if a record is filtered"""
    if not filter:
        return False

    if record.network.code in filter:
        return True

    if record.network_region in filter:
        return True

    return False
