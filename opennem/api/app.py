from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.admin.router import router as admin_router
from opennem.api.export.router import router as export_router
from opennem.api.facility.router import router as facility_router
from opennem.api.geo.router import router as geo_router
from opennem.api.locations import router as locations_router
from opennem.api.revision.router import router as revisions_router
from opennem.api.station.router import router as station_router
from opennem.api.stats.router import router as stats_router
from opennem.api.weather.router import router as weather_router
from opennem.core.time import INTERVALS, PERIODS
from opennem.core.units import UNITS
from opennem.db import get_database_session
from opennem.db.models.opennem import FuelTech, Network
from opennem.schema.network import NetworkSchema
from opennem.schema.opennem import FueltechSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.schema.units import UnitDefinition
from opennem.settings import settings
from opennem.utils.version import get_version

from .schema import FueltechResponse

app = FastAPI(
    title="OpenNEM", debug=settings.debug, version=get_version(as_string=True)
)

app.mount(
    "/static",
    StaticFiles(directory=settings.static_folder_path),
    name="static",
)

app.include_router(stats_router, tags=["Stats"], prefix="/stats")
app.include_router(locations_router, tags=["Locations"], prefix="/locations")
app.include_router(geo_router, tags=["Geo"], prefix="/geo")
app.include_router(station_router, tags=["Stations"], prefix="/station")
app.include_router(facility_router, tags=["Facilities"], prefix="/facility")
app.include_router(revisions_router, tags=["Revisions"], prefix="/revision")
app.include_router(weather_router, tags=["Weather"], prefix="/weather")
app.include_router(admin_router, tags=["Admin"], prefix="/admin")
app.include_router(export_router, tags=["Export"], prefix="/export")


origins = [
    "https://opennem.org.au",
    "https://dev.opennem.org.au",
    "https://admin.opennem.org.au",
    "https://admin.opennem.test",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/networks", response_model=List[NetworkSchema])
def networks(
    session: Session = Depends(get_database_session),
) -> List[NetworkSchema]:
    networks = session.query(Network).all()

    if not networks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    response = [NetworkSchema.parse_obj(i) for i in networks]

    return response


@app.get("/fueltechs", response_model=List[FueltechSchema])
def fueltechs(
    session: Session = Depends(get_database_session),
) -> FueltechResponse:
    fueltechs = session.query(FuelTech).all()

    if not fueltechs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    response = [FueltechSchema.parse_obj(i) for i in fueltechs]

    return response


@app.get("/intervals", response_model=List[TimeInterval])
def intervals() -> List[TimeInterval]:
    return INTERVALS


@app.get("/periods", response_model=List[TimePeriod])
def periods() -> List[TimePeriod]:
    return PERIODS


@app.get("/units", response_model=List[UnitDefinition])
def units() -> List[UnitDefinition]:
    return UNITS
