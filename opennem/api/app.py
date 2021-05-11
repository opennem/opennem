import logging
from typing import List

import aioredis
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import Query
from fastapi.responses import FileResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from opennem.api.admin.router import router as admin_router
from opennem.api.facility.router import router as facility_router
from opennem.api.geo.router import router as geo_router
from opennem.api.locations import router as locations_router
from opennem.api.schema import APINetworkRegion, APINetworkSchema
from opennem.api.station.router import router as station_router
from opennem.api.stats.router import router as stats_router
from opennem.api.tasks.router import router as tasks_router
from opennem.api.weather.router import router as weather_router
from opennem.core.time import INTERVALS, PERIODS
from opennem.core.units import UNITS
from opennem.db import database, get_database_session
from opennem.db.models.opennem import FuelTech, Network, NetworkRegion
from opennem.schema.opennem import FueltechSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.schema.units import UnitDefinition
from opennem.settings import settings
from opennem.utils.http_cache import PydanticCoder
from opennem.utils.version import get_version

logger = logging.getLogger(__name__)


app = FastAPI(
    title="OpenNEM", debug=settings.debug, version=get_version(), redoc_url="/docs", docs_url=None
)

try:
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/static",
        StaticFiles(directory=settings.static_folder_path),
        name="static",
    )
except Exception as e:
    logger.error("Error initializing static hosting: {}".format(e))


app.include_router(stats_router, tags=["Stats"], prefix="/stats")
app.include_router(locations_router, tags=["Locations"], prefix="/locations")
app.include_router(geo_router, tags=["Geo"], prefix="/geo")
app.include_router(station_router, tags=["Stations"], prefix="/station")
app.include_router(facility_router, tags=["Facilities"], prefix="/facility")
app.include_router(weather_router, tags=["Weather"], prefix="/weather")
app.include_router(admin_router, tags=["Admin"], prefix="/admin", include_in_schema=False)
app.include_router(tasks_router, tags=["Tasks"], prefix="/tasks", include_in_schema=False)


origins = [
    "https://opennem.org.au",
    "https://dev.opennem.org.au",
    "https://staging.opennem.org.au",
    "https://admin.opennem.org.au",
    "https://admin.opennem.test",
    "http://localhost:8001",
    "http://localhost:3000",
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)


# Custom exception handler
@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=418,
        content={"message": f"Error: {exc.args}"},
    )


@app.on_event("startup")
async def startup() -> None:
    logger.debug("In startup")
    # await database.connect()

    redis = await aioredis.create_redis_pool(settings.cache_url, encoding="utf-8")
    FastAPICache.init(RedisBackend(redis), prefix="api-cache", coder=PydanticCoder)


# @app.on_event("shutdown")
async def shutdown() -> None:
    logger.debug("In shutdown")
    await database.disconnect()


@app.get("/robots.txt", response_class=FileResponse, include_in_schema=False)
def robots_txt() -> FileResponse:
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(settings.static_folder_path + "/robots.txt")


@app.get("/alert_test", include_in_schema=False)
def alert_test() -> None:
    raise Exception("Test Alert Error from {}".format(settings.env))


@app.get("/exception_test", include_in_schema=False)
def exception_test() -> HTTPException:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Custom exception message"
    )


@app.get(
    "/networks",
    response_model=List[APINetworkSchema],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def networks(
    session: Session = Depends(get_database_session),
) -> List[APINetworkSchema]:
    networks = session.query(Network).join(Network.regions).all()

    if not networks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return networks


@app.get(
    "/networks/regions",
    response_model=List[APINetworkRegion],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def network_regions(
    session: Session = Depends(get_database_session),
    network_code: str = Query(None, description="Network code"),
) -> List[APINetworkRegion]:
    network_id = network_code.upper()

    network_regions = session.query(NetworkRegion).filter_by(network_id=network_id).all()

    if not network_regions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    response = [APINetworkRegion.parse_obj(i) for i in network_regions]

    return response


@app.get("/fueltechs", response_model=List[FueltechSchema])
def fueltechs(
    session: Session = Depends(get_database_session),
) -> List[FueltechSchema]:
    fueltechs = session.query(FuelTech).all()

    if not fueltechs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return fueltechs


@app.get("/intervals", response_model=List[TimeInterval])
def intervals() -> List[TimeInterval]:
    return INTERVALS


@app.get("/periods", response_model=List[TimePeriod])
def periods() -> List[TimePeriod]:
    return PERIODS


@app.get("/units", response_model=List[UnitDefinition])
def units() -> List[UnitDefinition]:
    return UNITS
