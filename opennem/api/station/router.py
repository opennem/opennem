import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from opennem.api import throttle
from opennem.api.exceptions import OpennemBaseHttpException
from opennem.api.schema import APIV4ResponseSchema
from opennem.cms.importer import get_cms_facilities
from opennem.db import get_scoped_session
from opennem.db.models.opennem import Facility, FuelTech, Location, Station

from .schema import StationsResponse

logger = logging.getLogger("opennem.api.station")

router = APIRouter()


class NetworkNotFound(OpennemBaseHttpException):
    detail = "Network not found"


class StationNotFound(OpennemBaseHttpException):
    detail = "Station not found"


class StationNoFacilities(OpennemBaseHttpException):
    detail = "Station has no facilities"


@throttle.throttle_request()
@router.get(
    "/",
    response_model=StationsResponse,
    description="Get a list of all stations",
    response_model_exclude_none=True,
)
async def get_stations(
    response: Response,
    session: AsyncSession = Depends(get_scoped_session),
    facilities_include: bool | None = True,
    only_approved: bool | None = False,
    name: str | None = None,
    limit: int | None = None,
    page: int = 1,
) -> StationsResponse:
    query = select(Station).join(Location)

    if facilities_include:
        query = query.outerjoin(Facility, Facility.station_id == Station.id).outerjoin(
            FuelTech, Facility.fueltech_id == FuelTech.code
        )

    if only_approved:
        query = query.where(Station.approved == True)  # noqa: E712

    if name:
        query = query.where(Station.name.like(f"%{name}%"))

    query = query.order_by(Station.name)

    if limit:
        query = query.limit(limit)

    result = await session.execute(query)
    stations = result.unique().scalars().all()

    resp = StationsResponse(data=stations, total_records=len(stations))

    response.headers["X-Total-Count"] = str(len(stations))

    return resp


@router.get(
    "/au/{network_id}/{station_code:path}",
    name="Get station information",
    description="Get a single station by code",
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
async def station(
    network_id: str,
    station_code: str,
) -> APIV4ResponseSchema:
    if network_id.upper() not in ["NEM", "WEM"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")

    facilities = get_cms_facilities(facility_code=station_code)

    if not facilities:
        raise StationNotFound()

    facility = facilities[0]

    if not facility.units:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    try:
        model = APIV4ResponseSchema(success=True, data=[facility], total_records=1)
    except Exception as e:
        logger.error(f"Error creating APIV4ResponseSchema: {e}")
        raise e

    return model
