from fastapi import APIRouter, HTTPException
from starlette import status

from opennem.api.geo.schema import FacilityGeo
from opennem.api.station.controllers import get_stations

from .controllers import stations_to_geojson

router = APIRouter()


@router.get("/facilities", name="Facility Geo", response_model=FacilityGeo, include_in_schema=False)
async def geo_facilities_api() -> FacilityGeo:
    stations = await get_stations(only_approved=True)

    if not stations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No stations found")

    stations_geo = await stations_to_geojson(stations)

    return stations_geo
