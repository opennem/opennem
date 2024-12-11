import logging

from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from fastapi_versionizer import api_version
from starlette import status

from opennem.api import throttle
from opennem.api.exceptions import OpennemBaseHttpException
from opennem.api.schema import APIV4ResponseSchema
from opennem.cms.importer import get_cms_facilities
from opennem.schema.unit import UnitFueltechType
from opennem.utils.dates import get_today_opennem
from opennem.utils.version import get_version

logger = logging.getLogger("opennem.api.station")

router = APIRouter()


class NetworkNotFound(OpennemBaseHttpException):
    detail = "Network not found"


class StationNotFound(OpennemBaseHttpException):
    detail = "Station not found"


class StationNoFacilities(OpennemBaseHttpException):
    detail = "Station has no facilities"


@throttle.throttle_request()
@api_version(4)
@cache(expire=60 * 5)
@router.get(
    "/",
    description="Get a list of all facilities",
    response_model_exclude_none=True,
)
async def get_facilities() -> APIV4ResponseSchema:
    facilities = get_cms_facilities()

    model_output = APIV4ResponseSchema(success=True, data=facilities, total_records=len(facilities))

    return model_output


@api_version(4)
@cache(expire=60 * 60)
@router.get(
    "/au/{network_id}/{station_code:path}",
    name="Get station information",
    description="Get a single station by code",
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
async def get_facility(
    network_id: str,
    station_code: str,
) -> APIV4ResponseSchema:
    if network_id.upper() not in ["NEM", "WEM"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")

    facilities = get_cms_facilities(facility_code=station_code)

    # remove 'battery' units
    facilities_clean = []

    for facility in facilities:
        units = [u for u in facility.units if u.fueltech_id != UnitFueltechType.battery]
        facility.units = units
        facilities_clean.append(facility)

    if not facilities:
        raise StationNotFound()

    facility = facilities[0]

    if not facility.units:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    try:
        model = APIV4ResponseSchema(
            version=get_version(),
            created_at=get_today_opennem(),
            success=True,
            data=[facility],
            total_records=1,
        )
    except Exception as e:
        logger.error(f"Error creating APIV4ResponseSchema: {e}")
        raise e

    return model
