from datetime import datetime

from fastapi import APIRouter
from fastapi_versioning import version

from opennem.recordreactor.schema import MilestoneRecord

from .queries import get_milestones

milestones_router = APIRouter(tags=["Milestones"], include_in_schema=True)


def map_milestone_records_from_db(db_records: list[dict]) -> list[MilestoneRecord]:
    """Map a list of milestone records from the database to MilestoneRecord"""
    milestone_records = []

    for db_record in db_records:
        milestone_record = {
            "instance_id": db_record["instance_id"],
            "record_id": db_record["record_id"].lower(),
            "dtime": db_record["dtime"],
            "record_type": db_record["record_type"],
            "significance": db_record["significance"],
            "value": float(db_record["value"]),
            "unit": "MW",
            "fueltech": db_record["fueltech_group_id"],
            "network": db_record["network_id"],
        }

        if db_record["network_region"]:
            milestone_record["network_region"] = db_record["network_region"]

        milestone_model = MilestoneRecord(**milestone_record)
        milestone_records.append(milestone_model)

    return milestone_records


@milestones_router.get("/")
@version(4)
def api_get_domains(
    limit: int = 100, page_number: int = 1, date_start: datetime | None = None, date_end: datetime | None = None
) -> list[MilestoneRecord]:
    """Get a list of milestones

    @TODO date filter

    """
    db_records = get_milestones(limit=limit, page_number=page_number)

    milestone_records = map_milestone_records_from_db(db_records)

    return milestone_records
