import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from fastapi_versionizer.versionizer import api_version
from starlette.exceptions import HTTPException

from opennem.api.schema import APIV4ResponseSchema
from opennem.recordreactor.schema import MilestoneRecord

from .queries import get_milestone_records

logger = logging.getLogger("opennem.api.milestones.router")

milestones_router = APIRouter(tags=["Milestones"], include_in_schema=True)


def map_milestone_records_from_db(db_records: list[dict]) -> list[MilestoneRecord]:
    """Map a list of milestone records from the database to MilestoneRecord"""
    milestone_records = []

    for db_record in db_records:
        milestone_interval: datetime = db_record["interval"]
        network_id: str = db_record["network_id"]

        if network_id != "WEM":
            milestone_interval = milestone_interval.astimezone(ZoneInfo("Australia/Brisbane"))
            milestone_interval += timedelta(hours=10)
        else:
            interval = milestone_interval.astimezone(ZoneInfo("Australia/Perth"))
            interval += timedelta(hours=8)

        milestone_record = {
            "instance_id": db_record["instance_id"],
            "record_id": db_record["record_id"].lower(),
            "interval": milestone_interval,
            "record_type": db_record["record_type"],
            "significance": db_record["significance"],
            "value": float(db_record["value"]),
            "unit": "MW",
            "description": db_record["description"],
            "fueltech": db_record["fueltech_group_id"],
            "network": db_record["network_id"],
            "period": db_record["period"],
        }

        if db_record["network_region"]:
            milestone_record["network_region"] = db_record["network_region"]

        milestone_model = MilestoneRecord(**milestone_record)
        milestone_records.append(milestone_model)

    return milestone_records


@milestones_router.get("/", response_model=APIV4ResponseSchema, response_model_exclude_unset=True, description="Get milestones")
@api_version(4)
async def get_milestones(
    limit: int = 100, page: int = 1, date_start: datetime | None = None, date_end: datetime | None = None
) -> APIV4ResponseSchema:
    """Get a list of milestones"""

    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be less than 1000")

    # if date_start and date_end have no timezone, default to NEM time
    if date_start and not date_start.tzinfo:
        date_start = date_start.astimezone(ZoneInfo("Australia/Brisbane"))
    elif date_start and date_start.utcoffset() == timedelta(0):
        date_start = date_start.astimezone(ZoneInfo("Australia/Brisbane"))

    if date_end and not date_end.tzinfo:
        date_end = date_end.astimezone(ZoneInfo("Australia/Brisbane"))
    elif date_end and date_end.utcoffset() == timedelta(0):
        date_end = date_end.astimezone(ZoneInfo("Australia/Brisbane"))

    if date_start == date_end:
        raise HTTPException(status_code=400, detail="Date start and date end cannot be the same")

    try:
        db_records, total_records = get_milestone_records(limit=limit, page_number=page, date_start=date_start, date_end=date_end)
    except Exception as e:
        logger.error(f"Error getting milestone records: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error getting milestone records")
        return response_schema

    try:
        milestone_records = map_milestone_records_from_db(db_records)
    except Exception as e:
        logger.error(f"Error mapping milestone records: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error mapping milestone records")
        return response_schema

    response_schema = APIV4ResponseSchema(success=True, data=milestone_records, total_records=total_records)

    return response_schema
