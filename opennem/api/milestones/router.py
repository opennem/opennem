import logging
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from fastapi_versionizer.versionizer import api_version
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException

from opennem.api.keys import api_protected
from opennem.api.schema import APIV4ResponseSchema
from opennem.core.units import get_unit_by_value
from opennem.db import get_scoped_session
from opennem.recordreactor.schema import (
    MILESTONE_SUPPORTED_NETWORKS,
    MilestoneAggregate,
    MilestoneMetric,
    MilestonePeriod,
    MilestoneRecord,
)
from opennem.schema.network import NetworkSchema

from .queries import get_milestone_record, get_milestone_records

logger = logging.getLogger("opennem.api.milestones.router")

milestones_router = APIRouter(tags=["Milestones"], include_in_schema=True)


def map_milestone_records_from_db(db_records: list[dict]) -> list[MilestoneRecord]:
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
            "value_unit": get_unit_by_value(db_record["value_unit"]) if db_record["value_unit"] else None,
            "description": db_record["description"],
            "fueltech": db_record["fueltech_group_id"],
            "network": db_record["network_id"],
            "period": db_record["period"],
            "previous_record_id": db_record["previous_record_id"],
            "metric": MilestoneMetric(db_record["metric"]) if db_record["metric"] else None,
        }

        if db_record["network_region"]:
            milestone_record["network_region"] = db_record["network_region"]

        milestone_model = MilestoneRecord(**milestone_record)
        milestone_records.append(milestone_model)

    return milestone_records


@api_version(4)
@api_protected()
@milestones_router.get(
    "/",
    response_model=APIV4ResponseSchema,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    description="Get milestones",
)
async def get_milestones(
    limit: int = 100,
    page: int = 1,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    aggregate: MilestoneAggregate | None = None,
    metric: MilestoneMetric | None = None,
    fuel_tech: list[str] | None = Query(None),
    network: list[str] | None = Query(None),
    network_region: list[str] | None = Query(None),
    period: list[MilestonePeriod] | None = Query(None),
    db: AsyncSession = Depends(get_scoped_session),
) -> APIV4ResponseSchema:
    """Get a list of milestones"""

    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be less than 100")

    # if date_start and date_end have no timezone, default to NEM time
    if date_start and not date_start.tzinfo:
        date_start = date_start.astimezone(ZoneInfo("Australia/Brisbane"))
    elif date_start and date_start.utcoffset() == timedelta(0):
        date_start = date_start.astimezone(ZoneInfo("Australia/Brisbane"))

    if date_end and not date_end.tzinfo:
        date_end = date_end.astimezone(ZoneInfo("Australia/Brisbane"))
    elif date_end and date_end.utcoffset() == timedelta(0):
        date_end = date_end.astimezone(ZoneInfo("Australia/Brisbane"))

    if date_start and date_end and date_start == date_end:
        raise HTTPException(status_code=400, detail="Date start and date end cannot be the same")

    if aggregate:
        if aggregate not in MilestoneAggregate.__members__.values():
            raise HTTPException(status_code=400, detail="Invalid aggregate type")

        aggregate = MilestoneAggregate[aggregate]

    if metric:
        if metric not in MilestoneMetric.__members__.values():
            raise HTTPException(status_code=400, detail="Invalid metric type")

        metric = MilestoneMetric[metric]

    network_schemas: list[NetworkSchema] = []
    network_supported_ids = [network.code for network in MILESTONE_SUPPORTED_NETWORKS]

    if network:
        if not all(network in network_supported_ids for network in network):
            raise HTTPException(status_code=400, detail=f"Invalid network: {', '.join(network)}")

        network_schemas = [n for n in MILESTONE_SUPPORTED_NETWORKS if n.code in network]
    else:
        network_schemas = MILESTONE_SUPPORTED_NETWORKS

    # get a flat list of all network regions
    network_supported_regions: list[str] = []
    for n in network_schemas:
        network_supported_regions.extend(n.regions if n.regions else [])

    if network_region:
        if not network:
            raise HTTPException(status_code=400, detail="Networks must be provided when network regions are provided")

        network_region = [n.upper() for n in network_region]

        if not all(network_region in network_supported_regions for network_region in network_region):
            raise HTTPException(status_code=400, detail=f"Invalid network region: {", ".join(network_region)}")

    if period:
        if not all(period in MilestonePeriod.__members__.values() for period in period):
            raise HTTPException(status_code=400, detail="Invalid period")

        period = [MilestonePeriod[period] for period in period]

    try:
        db_records, total_records = await get_milestone_records(
            db,
            limit=limit,
            page_number=page,
            date_start=date_start,
            date_end=date_end,
            aggregate=aggregate,
            fueltech=fuel_tech,
            metric=metric,
            networks=network_schemas,
            network_regions=network_region,
            periods=period,
        )
    except Exception as e:
        logger.error(f"Error getting milestone records: {e}")
        logger.exception(e)
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


@api_version(4)
@api_protected()
@milestones_router.get(
    "/{instance_id}",
    response_model=APIV4ResponseSchema,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    description="Get a single milestone",
)
async def get_milestone(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_scoped_session),
) -> APIV4ResponseSchema:
    """Get a single milestone"""

    try:
        db_record = await get_milestone_record(session=db, instance_id=instance_id)
    except Exception as e:
        logger.error(f"Error getting milestone record: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error getting milestone record")
        return response_schema

    if not db_record:
        raise HTTPException(status_code=404, detail="Milestone record not found")

    try:
        milestone_record = map_milestone_records_from_db([db_record])
    except Exception as e:
        logger.error(f"Error mapping milestone record: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error mapping milestone record")
        return response_schema

    response_schema = APIV4ResponseSchema(success=True, data=milestone_record)

    return response_schema
