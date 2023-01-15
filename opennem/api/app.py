"""
OpenNEM API

Primary Router. All the main setup of the API is here.
"""
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.param_functions import Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request

from opennem.api.admin.router import router as admin_router
from opennem.api.auth.router import router as auth_router
from opennem.api.exceptions import OpennemBaseHttpException, OpennemExceptionResponse
from opennem.api.facility.router import router as facility_router
from opennem.api.feedback.router import router as feedback_router
from opennem.api.geo.router import router as geo_router
from opennem.api.location.router import router as location_router
from opennem.api.locations import router as locations_router
from opennem.api.schema import APINetworkRegion, APINetworkSchema
from opennem.api.station.router import router as station_router
from opennem.api.stats.router import router as stats_router
from opennem.api.tasks.router import router as tasks_router
from opennem.api.weather.router import router as weather_router
from opennem.core.time import INTERVALS, PERIODS
from opennem.core.units import UNITS
from opennem.db import get_database_session
from opennem.db.models.opennem import FuelTech, Network, NetworkRegion
from opennem.schema.opennem import FueltechSchema, OpennemErrorSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.schema.units import UnitDefinition
from opennem.settings import settings
from opennem.utils.version import get_version

logger = logging.getLogger(__name__)


app = FastAPI(title="OpenNEM", debug=settings.debug, version=get_version(), redoc_url="/docs", docs_url=None)

# @TODO put CORS available/permissions in settings
origins = [
    "https://opennem.org.au",
    "https://dev.opennem.org.au",
    "https://staging.opennem.org.au",
    "https://admin.opennem.org.au",
    "https://admin.opennem.test",
    "http://localhost:8002",
    "http://127.0.0.1:8002",
    "https://admin.opennem.localhost",
    "https://*.opennem-fe.pages.dev",
]

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

        resp_content = OpennemErrorSchema(detail="Maintenance Mode")

        return OpennemExceptionResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, response_class=resp_content)

    response = await call_next(request)
    return response


# Custom exception handler
@app.exception_handler(OpennemBaseHttpException)
async def opennem_exception_handler(request: Request, exc: OpennemBaseHttpException) -> OpennemExceptionResponse:
    resp_content = OpennemErrorSchema(detail=exc.detail)

    return OpennemExceptionResponse(
        status_code=exc.status_code,
        response_class=resp_content,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> OpennemExceptionResponse:
    resp_content = OpennemErrorSchema(detail=exc.detail)

    return OpennemExceptionResponse(
        status_code=exc.status_code,
        response_class=resp_content,
    )


@app.exception_handler(401)
@app.exception_handler(403)
async def http_type_exception_handler(request: Request, exc: HTTPException) -> OpennemExceptionResponse:
    resp_content = OpennemErrorSchema(detail=exc.detail)

    return OpennemExceptionResponse(
        status_code=exc.status_code,
        response_class=resp_content,
    )


# sub-routers
app.include_router(auth_router, tags=["Authentication"], prefix="/auth", include_in_schema=False)
app.include_router(stats_router, tags=["Stats"], prefix="/stats")
app.include_router(locations_router, tags=["Locations"], prefix="/locations")
app.include_router(geo_router, tags=["Geo"], prefix="/geo")
app.include_router(location_router, tags=["Locations"], prefix="/location")
app.include_router(station_router, tags=["Stations"], prefix="/station")
app.include_router(facility_router, tags=["Facilities"], prefix="/facility")
app.include_router(weather_router, tags=["Weather"], prefix="/weather")
app.include_router(admin_router, tags=["Admin"], prefix="/admin", include_in_schema=False)
app.include_router(tasks_router, tags=["Tasks"], prefix="/tasks", include_in_schema=False)
app.include_router(feedback_router, tags=["Feedback"], prefix="/feedback", include_in_schema=False)


try:
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/static",
        StaticFiles(directory=settings.static_folder_path),
        name="static",
    )
except Exception as e:
    logger.info(f"Error initializing static hosting: {e}")


@app.get(
    "/robots.txt",
    response_class=FileResponse,
    include_in_schema=False,
)
def robots_txt() -> str:
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return f"{settings.static_folder_path}/robots.txt"


@app.get(
    "/networks",
    response_model=list[APINetworkSchema],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def networks(
    session: Session = Depends(get_database_session),
) -> list[APINetworkSchema]:
    networks = session.query(Network).join(Network.regions).all()

    if not networks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return networks


@app.get(
    "/networks/regions",
    response_model=list[APINetworkRegion],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def network_regions(
    session: Session = Depends(get_database_session),
    network_code: str = Query(..., description="Network code"),
) -> list[APINetworkRegion]:
    network_id = network_code.upper()

    network_regions = session.query(NetworkRegion).filter_by(network_id=network_id).all()

    if not network_regions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    logger.debug(network_regions)

    response = [APINetworkRegion(code=i.code, timezone=i.timezone) for i in network_regions]

    return response


@app.get("/fueltechs", response_model=list[FueltechSchema])
def fueltechs(
    session: Session = Depends(get_database_session),
) -> list[FueltechSchema]:
    fueltechs = session.query(FuelTech).all()

    if not fueltechs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return [FueltechSchema.from_orm(i) for i in fueltechs]


@app.get("/intervals", response_model=list[TimeInterval])
def intervals() -> list[TimeInterval]:
    return INTERVALS


@app.get("/periods", response_model=list[TimePeriod])
def periods() -> list[TimePeriod]:
    return PERIODS


@app.get("/units", response_model=list[UnitDefinition])
def units() -> list[UnitDefinition]:
    return UNITS
