import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import TypeAdapter
from starlette import status

from opennem.api import throttle
from opennem.api.cache_keys import tiered_key_builder
from opennem.api.exceptions import OpennemBaseHttpException
from opennem.api.response_cache import PreEncoded, cached_json
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.security import authenticated_user
from opennem.cms.importer import get_cms_facilities
from opennem.schema.unit import UnitFueltechType

logger = logging.getLogger("opennem.api.station")

router = APIRouter()

# `cached_json` sits BELOW `@router.get` so the route registers the caching wrapper (the old `@cache` above the
# router decorator wrapped a copy FastAPI never called, #744). `user: authenticated_user` is a normal dependency,
# so auth runs before the endpoint on cache hits too. Errors raise out of the handler and are never stored.
FACILITIES_CACHE_TTL = 60 * 5
FACILITY_CACHE_TTL = 60 * 60

_RESPONSE_ADAPTER: "TypeAdapter[APIV4ResponseSchema]" = TypeAdapter(APIV4ResponseSchema)

_inflight: dict[tuple[str, ...], "asyncio.Task[PreEncoded]"] = {}


def _flight_done(key: tuple[str, ...], task: "asyncio.Task[PreEncoded]") -> None:
    _inflight.pop(key, None)
    if not task.cancelled():
        task.exception()  # mark retrieved: waiters re-raise it, a lone cancelled waiter must not log "never retrieved"


async def _single_flight(key: tuple[str, ...], build: Callable[[], Awaitable[Any]]) -> PreEncoded:
    """Coalesce concurrent cache misses for one key into a single cms fetch + encode.

    The build result is serialised once (same settings as `cached_json`, so bytes are identical to a normal miss)
    and shared by every waiter. Awaiters are shielded so one cancelled client cannot kill the shared fetch.
    """
    task = _inflight.get(key)
    if task is None:

        async def run() -> PreEncoded:
            model = await build()
            body = await asyncio.to_thread(_RESPONSE_ADAPTER.dump_json, model, by_alias=True, exclude_none=True)
            return PreEncoded(body)

        task = asyncio.ensure_future(run())
        _inflight[key] = task
        task.add_done_callback(lambda t: _flight_done(key, t))
    return await asyncio.shield(task)


class NetworkNotFound(OpennemBaseHttpException):
    detail = "Network not found"


class StationNotFound(OpennemBaseHttpException):
    detail = "Station not found"


class StationNoFacilities(OpennemBaseHttpException):
    detail = "Station has no facilities"


@throttle.throttle_request()
@router.get(
    "/",
    description="Get a list of all facilities",
    response_model_exclude_none=True,
)
@cached_json(expire=FACILITIES_CACHE_TTL, key_builder=tiered_key_builder, return_type=APIV4ResponseSchema, exclude_none=True)
async def get_facilities(user: authenticated_user) -> APIV4ResponseSchema:
    async def build() -> APIV4ResponseSchema:
        facilities = await get_cms_facilities()
        return APIV4ResponseSchema(success=True, data=facilities, total_records=len(facilities))

    return await _single_flight(("facilities",), build)  # pyright: ignore[reportReturnType]


@router.get(
    "/au/{network_id}/{station_code:path}",
    name="Get station information",
    description="Get a single station by code",
    response_model_exclude_none=True,
    response_model_exclude_unset=False,
)
@cached_json(expire=FACILITY_CACHE_TTL, key_builder=tiered_key_builder, return_type=APIV4ResponseSchema, exclude_none=True)
async def get_facility(
    network_id: str,
    station_code: str,
    user: authenticated_user,
) -> APIV4ResponseSchema:
    if network_id.upper() not in ["NEM", "WEM"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")

    async def build() -> APIV4ResponseSchema:
        facilities = await get_cms_facilities(facility_code=station_code)

        if not facilities:
            raise StationNotFound()

        facility = facilities[0]
        # remove 'battery' units
        facility.units = [u for u in facility.units if u.fueltech_id != UnitFueltechType.battery]

        if not facility.units:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station has no facilities",
            )

        return APIV4ResponseSchema(success=True, data=[facility], total_records=1)

    return await _single_flight(("facility", station_code), build)  # pyright: ignore[reportReturnType]
