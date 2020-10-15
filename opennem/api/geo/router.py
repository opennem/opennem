from fastapi import APIRouter, Depends, HTTPException
from fastapi.param_functions import Query
from geojson_pydantic.features import FeatureCollection
from sqlalchemy.orm.session import Session
from starlette import status

from opennem.api.geo.schema import FacilityGeo
from opennem.api.station.controllers import get_stations
from opennem.db import get_database_session

from .controllers import stations_to_geojson

router = APIRouter()


@router.get(
    "/facilities", name="Facility Geo", response_model=FacilityGeo,
)
def geo_facilities_api(
    only_approved: bool = Query(
        True, description="Only show approved stations"
    ),
    session: Session = Depends(get_database_session),
) -> FacilityGeo:
    stations = get_stations(session, only_approved=only_approved)

    if not stations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No stations found"
        )

    stations_geo = stations_to_geojson(stations)

    return stations_geo
