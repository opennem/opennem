import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

from opennem.api.exceptions import OpennemBaseHttpException
from opennem.core.dispatch_type import DispatchType
from opennem.db import get_database_session
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


@router.get(
    "/",
    response_model=StationsResponse,
    description="Get a list of all stations",
    response_model_exclude_none=True,
)
def stations(
    response: Response,
    session: Session = Depends(get_database_session),
    facilities_include: bool | None = True,
    only_approved: bool | None = False,
    name: str | None = None,
    limit: int | None = None,
    page: int = 1,
) -> StationsResponse:
    stations = session.query(Station).join(Location).enable_eagerloads(True)

    if facilities_include:
        stations = stations.outerjoin(Facility, Facility.station_id == Station.id).outerjoin(
            FuelTech, Facility.fueltech_id == FuelTech.code
        )

    if only_approved:
        stations = stations.filter(Station.approved == True)  # noqa: E712

    if name:
        stations = stations.filter(Station.name.like(f"%{name}%"))

    stations = stations.order_by(
        Station.name,
    )

    if limit:
        stations = stations.limit(limit)

    stations = stations.all()

    resp = StationsResponse(data=stations, total_records=len(stations))

    response.headers["X-Total-Count"] = str(len(stations))

    return resp


@router.get(
    "/{id:int}",
    response_model=StationResponse,
    description="Get a single station record",
    response_model_exclude_none=False,
)
def station_record(
    response: Response,
    id: int,
    session: Session = Depends(get_database_session),
) -> StationResponse:
    logger.debug(f"get {id}")

    station = session.query(Station).get(id)

    if not station:
        raise StationNotFound()

    resp = StationResponse(record=station, total_records=1)

    response.headers["X-Total-Count"] = str(1)

    return resp


@router.get(
    "/{country_code}/{network_id}/{station_code:path}",
    response_model=StationOutputSchema,
    description="Get a single station by code",
    response_model_exclude_none=True,
    # response_model_exclude={"location": {"lat", "lng"}},
)
@cache(expire=60 * 60 * 6)
async def station(
    country_code: str,
    network_id: str,
    station_code: str,
    session: Session = Depends(get_database_session),
    only_generators: bool | None = True,
) -> Station:
    station_query = (
        session.query(Station)
        .filter(Station.code == station_code)
        .filter(Facility.station_id == Station.id)
        .filter(~Facility.code.endswith("NL1"))
        .filter(Facility.network_id == network_id)
        .filter(Network.country == country_code)
    )

    if only_generators:
        station_query = station_query.filter(Facility.dispatch_type == DispatchType.GENERATOR)

    station = station_query.one_or_none()

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
