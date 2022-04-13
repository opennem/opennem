import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette.responses import Response

from opennem.api.exceptions import OpennemBaseHttpException
from opennem.db import get_database_session
from opennem.db.models.opennem import Location

from .schema import LocationResponse, LocationsResponse

logger = logging.getLogger("opennem.api.location")

router = APIRouter()


class LocationNotFound(OpennemBaseHttpException):
    detail = "Location not found"


@router.get(
    "/",
    response_model=LocationsResponse,
    description="Get a list of all locations",
    response_model_exclude_none=True,
)
def locations(
    response: Response,
    session: Session = Depends(get_database_session),
    limit: Optional[int] = None,
    page: int = 1,
    id: Optional[List[str]] = Query(None),
) -> LocationsResponse:
    location_query = session.query(Location).enable_eagerloads(True)
    locations: List[Location] = []

    if id:
        location_query = location_query.filter(Location.id.in_(id))

    if limit:
        location_query = location_query.limit(limit)

    location_query = location_query.order_by(
        Location.id,
    )

    locations = location_query.all()

    if not locations:
        raise LocationNotFound()

    resp = LocationsResponse(data=locations, total_records=len(locations))

    response.headers["X-Total-Count"] = str(len(locations))

    return resp


@router.get(
    "/{id:int}",
    response_model=LocationResponse,
    description="Get a single location record",
    response_model_exclude_none=False,
)
def station_record(
    response: Response,
    id: int,
    session: Session = Depends(get_database_session),
) -> LocationsResponse:
    station = session.query(Location).get(id)

    if not station:
        raise LocationNotFound()

    resp = LocationResponse(record=station, total_records=1)

    response.headers["X-Total-Count"] = str(1)

    return resp
