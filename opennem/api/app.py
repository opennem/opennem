"""
OpenNEM API

Primary Router. All the main setup of the API is here.
"""

import logging
from contextlib import asynccontextmanager

import logfire
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import Query
from fastapi.responses import FileResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_versionizer import api_version
from fastapi_versionizer.versionizer import Versionizer
from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from opennem import settings
from opennem.api.data.router import router as data_router
from opennem.api.exceptions import OpennemBaseHttpException, OpennemExceptionResponse
from opennem.api.facilities.router import router as facilities_router
from opennem.api.feedback.router import router as feedback_router
from opennem.api.market.router import router as market_router
from opennem.api.milestones.router import milestones_router
from opennem.api.schema import APINetworkRegion, APINetworkSchema
from opennem.api.security import authenticated_user
from opennem.api.station.router import router as station_router
from opennem.api.stats.router import router as stats_router
from opennem.api.webhooks.router import router as webhooks_router
from opennem.clients.unkey import unkey_client
from opennem.core.time import INTERVALS, PERIODS
from opennem.core.units import UNITS
from opennem.db import get_read_session
from opennem.db.models.opennem import FuelTech, Network, NetworkRegion
from opennem.schema.opennem import FueltechSchema, OpennemErrorSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.schema.units import UnitDefinition
from opennem.users.schema import OpennemUserResponse
from opennem.utils.host import get_hostname
from opennem.utils.version import get_version

logger = logging.getLogger("opennem.api")


# lifecycle events


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for the API
    """
    # Startup logic

    logfire.info(f"OpenElectricity API starting up on {settings.env}: v{get_version()} on host {get_hostname()}", service="api")

    if settings.is_dev:
        logger.info("Cache disabled")
        FastAPICache.init(backend=InMemoryBackend())
    else:
        redis = await aioredis.from_url(str(settings.redis_url), encoding="utf8", decode_responses=True)
        FastAPICache.init(RedisBackend(redis), prefix="api-cache")
        logger.info("Enabled API cache")

    await unkey_client.start()

    yield

    # Shutdown logic
    await unkey_client.close()


app = FastAPI(
    title="OpenElectricity", debug=settings.debug, version=get_version(), redoc_url="/docs", docs_url=None, lifespan=lifespan
)

logfire.instrument_fastapi(app)

# @TODO put CORS available/permissions in settings
origins = [
    "https://*.pages.dev",
    "https://*.oedev.org",
    "https://openelectricity.org.au",
    "https://explore.openelectricity.org.au",
    "http://localhost:3000",
    "http://localhost:5173",
]

if settings.is_dev:
    origins = ["*"]  # Allow all origins in development mode


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-ONAU", "X-ONAA"],
)


#  Maintenance mode middleware
@app.middleware("http")
async def intercept_maintenance_mode(request: Request, call_next):  # type: ignore
    if settings.maintenance_mode:
        logger.debug("Maintenance mode")

        resp_content = OpennemErrorSchema(error="Maintenance Mode")

        return OpennemExceptionResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, response_class=resp_content)

    response = await call_next(request)
    return response


# Custom exception handler
@app.exception_handler(OpennemBaseHttpException)
async def opennem_exception_handler(request: Request, exc: OpennemBaseHttpException) -> OpennemExceptionResponse:
    resp_content = OpennemErrorSchema(error=exc.detail)

    return OpennemExceptionResponse(
        status_code=exc.status_code,
        response_class=resp_content,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> OpennemExceptionResponse:
    logger.debug(f"HTTP Exception: {exc.status_code} {exc.detail}")

    resp_content = OpennemErrorSchema(error=exc.detail, success=False)

    return OpennemExceptionResponse(
        status_code=exc.status_code,
        response_class=resp_content,
    )


@app.exception_handler(401)
@app.exception_handler(403)
async def http_type_exception_handler(request: Request, exc: HTTPException) -> OpennemExceptionResponse:
    resp_content = OpennemErrorSchema(error=exc.detail)

    return OpennemExceptionResponse(
        status_code=exc.status_code,
        response_class=resp_content,
    )


# log API requests
api_request_counter = logfire.metric_counter("api_request_counter")
api_exception_counter = logfire.metric_counter("api_exception_counter")


# @app.middleware("http")
# async def log_api_request(request: Request, call_next):
#     api_request_counter.add(1)
#     response = await call_next(request)
#     return response


# @app.exception_handler(Exception)
# async def log_api_exception(request: Request, exc: Exception):
#     api_exception_counter.add(1)
#     return await http_exception_handler(request, exc)


# sub-routers
app.include_router(stats_router, tags=["Stats"], prefix="/stats", include_in_schema=False)
app.include_router(station_router, tags=["Facilities"], prefix="/facility", include_in_schema=False)
app.include_router(facilities_router, tags=["Facilities"], prefix="/facilities")
app.include_router(feedback_router, tags=["Feedback"], prefix="/feedback", include_in_schema=False)
app.include_router(milestones_router, tags=["Milestones"], prefix="/milestones", include_in_schema=False)
app.include_router(webhooks_router, tags=["Webhooks"], prefix="/webhooks", include_in_schema=False)
app.include_router(data_router, tags=["Data"], prefix="/data")
app.include_router(market_router, tags=["Market"], prefix="/market")

# new v4 routes
try:
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/static",
        StaticFiles(directory=settings.static_folder_path),
        name="static",
    )
except Exception as e:
    logger.info(f"Error initializing static hosting: {e}")


# static files
@app.get(
    "/robots.txt",
    response_class=FileResponse,
    include_in_schema=False,
)
async def robots_txt() -> str:
    return f"{settings.static_folder_path}/robots.txt"


@app.get(
    "/favicon.ico",
    response_class=FileResponse,
    include_in_schema=False,
)
async def favicon_ico() -> str:
    return f"{settings.static_folder_path}/favicon.png"


# base routes for types
@api_version(4)
@app.get(
    "/networks",
    response_model=list[APINetworkSchema],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    include_in_schema=False,
    tags=["Core"],
    description="Get networks",
)
async def get_networks() -> list[APINetworkSchema]:
    """
    Retrieve all networks with their associated regions.

    Args:
        session (AsyncSession): The database session.

    Returns:
        list[APINetworkSchema]: A list of network schemas.

    Raises:
        HTTPException: If no networks are found or if there's an error.

    """
    async with get_read_session() as session:
        stmt = select(Network).join(NetworkRegion, NetworkRegion.network_id == Network.code).distinct()
        result = await session.execute(stmt)
        networks = result.scalars().all()

        if not networks:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No networks found")

        return [APINetworkSchema.from_orm(network) for network in networks]


@api_version(3)
@app.get(
    "/networks/regions",
    response_model=list[APINetworkRegion],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    include_in_schema=False,
    tags=["Core"],
    description="Get network regions",
)
async def get_network_regions(
    session: AsyncSession = Depends(get_read_session),
    network_code: str = Query(..., description="Network code"),
) -> list[APINetworkRegion]:
    network_id = network_code.upper()

    network_regions = await session.execute(select(NetworkRegion).where(NetworkRegion.network_id == network_id))
    network_regions = network_regions.scalars().all()

    if not network_regions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    logger.debug(network_regions)

    response = [APINetworkRegion(code=i.code, timezone=i.timezone) for i in network_regions]

    return response


@api_version(4)
@app.get(
    "/fueltechs",
    response_model=list[FueltechSchema],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    include_in_schema=False,
    tags=["Core"],
    description="Get all fueltechs",
)
async def fueltechs(
    session: AsyncSession = Depends(get_read_session),
) -> list[FueltechSchema]:
    fueltechs = await session.execute(select(FuelTech))
    fueltechs = fueltechs.scalars().all()

    if not fueltechs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        models = [
            FueltechSchema(
                code=i.code,
                label=i.label,
                renewable=i.renewable,
            )
            for i in fueltechs
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid fueltechs") from e

    return models


@api_version(3)
@app.get(
    "/intervals",
    response_model=list[TimeInterval],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    include_in_schema=False,
    tags=["Core"],
    description="Get all intervals",
)
def intervals() -> list[TimeInterval]:
    return INTERVALS


@api_version(3)
@app.get(
    "/periods",
    response_model=list[TimePeriod],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    include_in_schema=False,
    tags=["Core"],
    description="Get all periods",
)
def periods() -> list[TimePeriod]:
    return PERIODS


@api_version(3)
@app.get(
    "/units",
    response_model=list[UnitDefinition],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    include_in_schema=False,
    tags=["Core"],
    description="Get all units",
)
def units() -> list[UnitDefinition]:
    return UNITS


@app.get("/health", include_in_schema=False)
def health_check() -> str:
    """Health check"""
    return "OK"


@api_version(4)
@app.get(
    "/me",
    response_model=OpennemUserResponse,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    tags=["User"],
    description="Get the current user",
)
async def get_user_me(user: authenticated_user) -> OpennemUserResponse:
    return OpennemUserResponse(data=user)


@app.get("/sentry-debug", include_in_schema=False)
def trigger_error():
    division_by_zero = 1 / 0  # noqa: F823, F841
    return "OK"


versions = Versionizer(
    app=app,
    prefix_format="/v{major}",
    semantic_version_format="{major}.{minor}",
    latest_prefix="",
    sort_routes=True,
    # default_version="v{major}",
).versionize()


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
