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
from opennem.db import get_scoped_session
from opennem.recordreactor.controllers import map_milestone_output_records_from_db
from opennem.recordreactor.schema import (
    MILESTONE_SUPPORTED_NETWORKS,
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestoneMetadataSchema,
    MilestonePeriod,
    MilestoneType,
)
from opennem.schema.network import NetworkSchema

from .queries import get_milestone_record, get_milestone_record_ids, get_milestone_records

logger = logging.getLogger("opennem.api.milestones.router")

milestones_router = APIRouter(tags=["Milestones"], include_in_schema=True)


@api_version(4)
@api_protected()
@milestones_router.get(
    "/records",
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
    milestone_type: list[MilestoneType] | None = Query(None, description="Milestone type filter"),
    fueltech_id: list[str] | None = Query(None),
    network: list[str] | None = Query(None),
    record_filter: list[str] | None = Query(None, description="Network filter - specify network or network_region ids"),
    network_region: list[str] | None = Query(None),
    significance: int | None = Query(None, description="Significance filter"),
    significance_min: int | None = Query(None, description="Significance minimum filter"),
    significance_max: int | None = Query(None, description="Significance maximum filter"),
    record_id_filter: str | None = Query(None, description="Filter by record_id - supports wildcards"),
    period: list[MilestonePeriod] | None = Query(None, description="Period filter"),
    db: AsyncSession = Depends(get_scoped_session),
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

    if date_start and date_end and date_start == date_end:
        raise HTTPException(status_code=400, detail="Date start and date end cannot be the same")

    if aggregate:
        if aggregate not in MilestoneAggregate.__members__.values():
            raise HTTPException(status_code=400, detail="Invalid aggregate type")

        aggregate = MilestoneAggregate[aggregate]

    milestone_type_query: list[str] = []

    if milestone_type:
        for m in milestone_type:
            milestone_type_query.append(MilestoneType(m))

    network_schemas: list[NetworkSchema] = []
    network_supported_ids = [network.code for network in MILESTONE_SUPPORTED_NETWORKS]

    if network:
        if not all(network in network_supported_ids for network in network):
            raise HTTPException(status_code=400, detail=f"Invalid network: {", ".join(network)}")

        network_schemas = [n for n in MILESTONE_SUPPORTED_NETWORKS if n.code in network]

    # get a flat list of all network regions
    network_supported_regions: list[str] = []
    for n in MILESTONE_SUPPORTED_NETWORKS:
        network_supported_regions.extend(n.regions or [])

    if network_region:
        if not network:
            raise HTTPException(status_code=400, detail="Networks must be provided when network regions are provided")

        network_region = [n.upper() for n in network_region]

        if not all(network_region in network_supported_regions for network_region in network_region):
            raise HTTPException(status_code=400, detail=f"Invalid network region: {", ".join(network_region)}")

    # filter by either network or network_region
    if record_filter:
        supported_networks_and_regions = network_supported_ids + network_supported_regions
        if not all(f in supported_networks_and_regions for f in record_filter):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter: {", ".join(record_filter)} not in {", ".join(supported_networks_and_regions)}",
            )

    if period:
        if not all(period in MilestonePeriod.__members__.values() for period in period):
            raise HTTPException(status_code=400, detail="Invalid period")

        period = [MilestonePeriod[period] for period in period]

    if significance:
        if not 0 <= significance <= 10:
            raise HTTPException(status_code=400, detail="Significance must be between 0 and 10")

        if significance_max or significance_min:
            raise HTTPException(status_code=400, detail="Cannot use significance with significance_min or significance_max")

    if significance_min and significance_max:
        if significance_min > significance_max:
            raise HTTPException(status_code=400, detail="Significance minimum must be less than significance maximum")

        if significance_max < 0 or significance_max > 10:
            raise HTTPException(status_code=400, detail="Significance maximum must be between 0 and 10")

    try:
        db_records, total_records = await get_milestone_records(
            db,
            limit=limit,
            page_number=page,
            date_start=date_start,
            date_end=date_end,
            aggregate=aggregate,
            fueltech_id=fueltech_id,
            milestone_types=milestone_type_query,
            networks=network_schemas,
            network_regions=network_region,
            record_filter=record_filter,
            record_id_filter=record_id_filter,
            significance=significance,
            significance_min=significance_min,
            significance_max=significance_max,
            periods=period,
        )
    except Exception as e:
        logger.error(f"Error getting milestone records: {e}")
        logger.exception(e)
        response_schema = APIV4ResponseSchema(success=False, error="Error getting milestone records")
        return response_schema

    try:
        milestone_records = map_milestone_output_records_from_db(db_records)
    except Exception as e:
        logger.error(f"Error mapping milestone records: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error mapping milestone records")
        return response_schema

    response_schema = APIV4ResponseSchema(success=True, data=milestone_records, total_records=total_records)

    return response_schema


@api_version(4)
@api_protected()
@milestones_router.get(
    "/history/{record_id}",
    response_model=APIV4ResponseSchema,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    description="Get a single milestone",
)
async def get_milestone_by_record_id(
    record_id: str,
    limit: int = 1000,
    page: int = 1,
    db: AsyncSession = Depends(get_scoped_session),
) -> APIV4ResponseSchema:
    """Get a single milestone by record id"""

    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be less than 1000")

    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")

    try:
        db_record, total_records = await get_milestone_records(session=db, record_id=record_id, page_number=page, limit=limit)
    except Exception as e:
        logger.error(f"Error getting milestone record: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error getting milestone record")
        return response_schema

    try:
        milestone_record = map_milestone_output_records_from_db(db_records=db_record)
    except Exception as e:
        logger.error(f"Error mapping milestone record: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error mapping milestone record")
        return response_schema

    if not db_record:
        raise HTTPException(status_code=404, detail="Milestone record not found")

    response_schema = APIV4ResponseSchema(success=True, data=milestone_record, total_records=total_records)

    return response_schema


@api_version(4)
@api_protected()
@milestones_router.get(
    "/instance/{instance_id}",
    response_model=APIV4ResponseSchema,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    description="Get a single milestone",
)
async def get_milestone(
    instance_id: uuid.UUID,
    include_history: bool = Query(False, description="Include historical milestone records"),
    db: AsyncSession = Depends(get_scoped_session),
) -> APIV4ResponseSchema:
    """Get a single milestone"""

    try:
        db_record = await get_milestone_record(session=db, instance_id=instance_id, include_history=include_history)
    except Exception as e:
        logger.error(f"Error getting milestone record: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error getting milestone record")
        return response_schema

    if not db_record:
        raise HTTPException(status_code=404, detail="Milestone record not found")

    try:
        milestone_record = map_milestone_output_records_from_db([db_record])
    except Exception as e:
        logger.error(f"Error mapping milestone record: {e}")
        response_schema = APIV4ResponseSchema(success=False, error="Error mapping milestone record")
        return response_schema

    if db_record["history"] and include_history:
        try:
            history_record_schemas = map_milestone_output_records_from_db(db_record["history"])
        except Exception as e:
            logger.error(f"Error mapping milestone record history: {e}")
            response_schema = APIV4ResponseSchema(success=False, error="Error mapping milestone record history")
            return response_schema

        milestone_record[0].history = history_record_schemas

    response_schema = APIV4ResponseSchema(success=True, data=milestone_record)

    return response_schema


@api_version(4)
@api_protected()
@milestones_router.get(
    "/record_id",
    response_model=APIV4ResponseSchema,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    description="Get a list of milestone record ids with the most recent record for each record_id",
    include_in_schema=True,
)
async def api_get_milestone_record_ids(
    db: AsyncSession = Depends(get_scoped_session),
    record_id: str | None = Query(None, description="Filter by record_id"),
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    aggregate: MilestoneAggregate | None = None,
    milestone_type: list[MilestoneType] | None = Query(None, description="Milestone type filter"),
    fueltech_id: list[str] | None = Query(None),
    network: list[str] | None = Query(None),
    network_region: list[str] | None = Query(None),
    significance: int | None = Query(None, description="Significance filter"),
    significance_min: int | None = Query(None, description="Significance minimum filter"),
    significance_max: int | None = Query(None, description="Significance maximum filter"),
) -> APIV4ResponseSchema:
    """Get a list of milestone record ids with the most recent record for each record_id"""

    network_schemas: list[NetworkSchema] = []
    network_supported_ids = [network.code for network in MILESTONE_SUPPORTED_NETWORKS]

    if network:
        if not all(network in network_supported_ids for network in network):
            raise HTTPException(status_code=400, detail=f"Invalid network: {", ".join(network)}")

        network_schemas = [n for n in MILESTONE_SUPPORTED_NETWORKS if n.code in network]

    # get a flat list of all network regions
    network_supported_regions: list[str] = []
    for n in MILESTONE_SUPPORTED_NETWORKS:
        network_supported_regions.extend(n.regions or [])

    if network_region:
        if not network:
            raise HTTPException(status_code=400, detail="Networks must be provided when network regions are provided")

        network_region = [n.upper() for n in network_region]

        if not all(network_region in network_supported_regions for network_region in network_region):
            raise HTTPException(status_code=400, detail=f"Invalid network region: {", ".join(network_region)}")

    if significance and (significance_min or significance_max):
        raise HTTPException(status_code=400, detail="Cannot use significance with significance_min or significance_max")

    if not significance:
        significance = 0

    if significance and (significance < 0 or significance > 10):
        raise HTTPException(status_code=400, detail="Significance must be between 0 and 10")

    if significance_max and (significance_max < 0 or significance_max > 10):
        raise HTTPException(status_code=400, detail="Significance maximum must be between 0 and 10")

    if significance_min and (significance_min < 0 or significance_min > 10):
        raise HTTPException(status_code=400, detail="Significance minimum must be between 0 and 10")

    if significance_min and significance_max:
        if significance_min > significance_max:
            raise HTTPException(status_code=400, detail="Significance minimum must be less than significance maximum")

        if significance_max < 0 or significance_max > 10:
            raise HTTPException(status_code=400, detail="Significance maximum must be between 0 and 10")

    record_ids = await get_milestone_record_ids(
        session=db,
        record_id=record_id,
        date_start=date_start,
        date_end=date_end,
        aggregate=aggregate,
        milestone_type=milestone_type,
        fueltech_id=fueltech_id,
        network=network,
        network_region=network_region,
        network_schemas=network_schemas,
        significance=significance,
        significance_min=significance_min,
        significance_max=significance_max,
    )

    if not record_ids:
        raise HTTPException(status_code=404, detail="No records found")

    return APIV4ResponseSchema(success=True, data=record_ids)


@api_version(4)
@api_protected()
@milestones_router.get(
    "/metadata",
    response_model=MilestoneMetadataSchema,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    description="Get metadata for milestones",
)
async def get_milestone_metadata() -> MilestoneMetadataSchema:
    """Get metadata for milestones"""

    metadata = MilestoneMetadataSchema(
        aggregates=list(MilestoneAggregate),
        milestone_type=list(MilestoneType),
        periods=list(MilestonePeriod),
        fueltechs=list(MilestoneFueltechGrouping),
        networks=MILESTONE_SUPPORTED_NETWORKS,
    )

    return metadata

    # response_schema = APIV4ResponseSchema(success=True, data=metadata.dict())
    # return response_schema
