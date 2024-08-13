import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit_by_value
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneMetric,
    MilestoneRecordOutputSchema,
)

logger = logging.getLogger("opennem.recordreactor.controllers")


def map_milestone_output_records_from_db(db_records: list[dict]) -> list[MilestoneRecordOutputSchema]:
    """Map a list of milestone records from the database to MilestoneRecord"""
    milestone_records = []

    for db_record in db_records:
        milestone_interval: datetime = db_record["interval"]
        network_id: str = db_record["network_id"]

        if network_id != "WEM":
            milestone_interval = milestone_interval.replace(tzinfo=ZoneInfo("Australia/Brisbane"))
        else:
            milestone_interval = milestone_interval.replace(tzinfo=ZoneInfo("Australia/Perth"))

        milestone_record = {
            "instance_id": db_record["instance_id"],
            "record_id": db_record["record_id"].lower(),
            "interval": milestone_interval,
            "aggregate": MilestoneAggregate(db_record["aggregate"]) if db_record["aggregate"] else None,
            "significance": db_record["significance"],
            "value": float(db_record["value"]),
            "unit": get_unit_by_value(db_record["value_unit"]) if db_record["value_unit"] else None,
            "description": db_record["description"],
            "network": network_from_network_code(db_record["network_id"]),
            "period": db_record["period"],
            "previous_instance_id": db_record["previous_instance_id"],
            "metric": MilestoneMetric(db_record["metric"]) if db_record["metric"] else None,
        }

        if db_record["network_region"]:
            milestone_record["network_region"] = db_record["network_region"]

        if db_record["fueltech_id"]:
            milestone_record["fueltech_id"] = db_record["fueltech_id"]

        milestone_model = MilestoneRecordOutputSchema(**milestone_record)
        milestone_records.append(milestone_model)

    return milestone_records
