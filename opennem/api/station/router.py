import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status
from starlette.responses import Response

from opennem.api import throttle
from opennem.api.exceptions import OpennemBaseHttpException
from opennem.core.dispatch_type import DispatchType
from opennem.db import get_scoped_session
from opennem.db.models.opennem import Facility, FuelTech, Location, Network, Station
from opennem.schema.opennem import StationOutputSchema

from .schema import StationResponse, StationsResponse

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
    "/{id:int}",
    response_model=StationResponse,
    description="Get a single station record",
    response_model_exclude_none=False,
)
async def station_record(
    response: Response,
    id: int,
    session: AsyncSession = Depends(get_scoped_session),
) -> StationResponse:
    logger.debug(f"get {id}")

    result = await session.execute(select(Station).where(Station.id == id))
    station = result.scalar_one_or_none()

    if not station:
        raise StationNotFound()

    resp = StationResponse(record=station, total_records=1)

    response.headers["X-Total-Count"] = str(1)

    return resp


@router.get(
    "/au/{network_id}/{station_code:path}",
    name="Get station information",
    description="Get a single station by code",
    response_model=StationOutputSchema,
    response_model_exclude_none=True,
)
async def station(
    network_id: str,
    station_code: str,
    only_generators: bool | None = True,
    session: AsyncSession = Depends(get_scoped_session),
) -> Station:
    if network_id.upper() not in ["NEM", "WEM"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")

    query = (
        select(Station)
        .join(Facility, Facility.station_id == Station.id)
        .join(Network, Network.code == Facility.network_id)
        .join(Location, Location.id == Station.location_id)
        .where(Station.code == station_code)
        .where(Network.code == network_id)
        .where(Facility.dispatch_type == DispatchType.GENERATOR)
        .options(joinedload(Station.facilities))
    )

    if only_generators:
        query = query.where(Facility.dispatch_type == DispatchType.GENERATOR)

    result = await session.execute(query)
    station = result.unique().scalar_one_or_none()

    if not station:
        raise StationNotFound()

    if not station.facilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    if station.facilities:
        station.network = station.facilities[0].network_id  # type: ignore

    return station
