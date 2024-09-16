import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from opennem.core.fueltech_group import get_fueltech_group
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit_by_value
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestonePeriod,
    MilestoneRecordOutputSchema,
    MilestoneRecordSchema,
    MilestoneType,
)

logger = logging.getLogger("opennem.recordreactor.controllers")


def map_milestone_output_records_from_db(db_records: list[dict]) -> list[MilestoneRecordOutputSchema]:
    """Map a list of milestone records from the database to MilestoneRecord"""
    milestone_records = []

    for db_record in db_records:
        milestone_interval: datetime = db_record["interval"]
        network_id: str = db_record["network_id"]
        network = network_from_network_code(network_id)

        # make outputs timezone aware
        milestone_interval = milestone_interval.replace(tzinfo=ZoneInfo(network.timezone))

        milestone_record = {
            "instance_id": db_record["instance_id"],
            "record_id": db_record["record_id"].lower(),
            "interval": milestone_interval,
            "aggregate": MilestoneAggregate(db_record["aggregate"]) if db_record["aggregate"] else None,
            "period": db_record["period"],
            "metric": MilestoneType(db_record["metric"]) if db_record["metric"] else None,
            "network_id": db_record["network_id"],
            "significance": db_record["significance"],
            "value": float(db_record["value"]),
            "value_unit": db_record["value_unit"],
            "description": db_record["description"],
            "previous_instance_id": db_record["previous_instance_id"],
        }

        if db_record["network_region"]:
            milestone_record["network_region"] = db_record["network_region"]

        if db_record["fueltech_id"]:
            milestone_record["fueltech_id"] = db_record["fueltech_id"]

        milestone_model = MilestoneRecordOutputSchema(**milestone_record)
        milestone_records.append(milestone_model)

    return milestone_records


def map_milestone_schema_from_db(db_records: list[dict]) -> list[MilestoneRecordSchema]:
    """Map a list of milestone records from the database to MilestoneRecordSchema"""
    milestone_records = []

    for db_record in db_records:
        milestone_interval: datetime = db_record["interval"]
        network_id: str = db_record["network_id"]
        network = network_from_network_code(network_id)

        if network_id != "WEM":
            milestone_interval = milestone_interval.replace(tzinfo=ZoneInfo("Australia/Brisbane"))
        else:
            milestone_interval = milestone_interval.replace(tzinfo=ZoneInfo("Australia/Perth"))

        milestone_record = {
            "interval": milestone_interval,
            "aggregate": MilestoneAggregate(db_record["aggregate"]) if db_record["aggregate"] else None,
            "metric": MilestoneType(db_record["metric"]) if db_record["metric"] else None,
            "period": MilestonePeriod(db_record["period"]),
            "unit": get_unit_by_value(db_record["value_unit"]),
            "network": network,
            "value": float(db_record["value"]),
        }

        if db_record["network_region"]:
            milestone_record["network_region"] = db_record["network_region"]

        if db_record["fueltech_id"]:
            milestone_record["fueltech_id"] = get_fueltech_group(db_record["fueltech_id"])

        milestone_model = MilestoneRecordSchema(**milestone_record)
        milestone_records.append(milestone_model)

    return milestone_records


def map_milestone_output_schema_to_record(milestone: MilestoneRecordOutputSchema) -> MilestoneRecordSchema:
    """Map a MilestoneRecordOutputSchema to a MilestoneRecordSchema"""
    milestone_record = {
        "interval": milestone.interval,
        "aggregate": MilestoneAggregate(milestone.aggregate),
        "metric": MilestoneType(milestone.metric),
        "period": MilestonePeriod(milestone.period),
        "unit": get_unit_by_value(milestone.value_unit),
        "network": network_from_network_code(milestone.network_id),
        "value": milestone.value,
    }

    if milestone.network_region:
        milestone_record["network_region"] = milestone.network_region

    if milestone.fueltech_id:
        milestone_record["fueltech"] = get_fueltech_group(milestone.fueltech_id)

    milestone_model = MilestoneRecordSchema(**milestone_record)
    return milestone_model
