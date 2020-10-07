from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.admin.router import router as admin_router
from opennem.api.facility.router import router as facility_router
from opennem.api.locations import router as locations_router
from opennem.api.revision.router import router as revisions_router
from opennem.api.station.router import router as station_router
from opennem.api.stats.router import router as stats_router
from opennem.api.weather.router import router as weather_router
from opennem.db import get_database_session
from opennem.db.models.opennem import (
    Facility,
    FuelTech,
    Location,
    Network,
    Revision,
    Station,
)
from opennem.schema.opennem import FueltechSchema, NetworkSchema

from .schema import FueltechResponse

app = FastAPI(title="OpenNEM", debug=True, version="3.0.0-alpha.3")

app.include_router(stats_router, tags=["Stats"], prefix="/stats")
app.include_router(locations_router, tags=["Locations"], prefix="/locations")
app.include_router(station_router, tags=["Stations"], prefix="/station")
app.include_router(facility_router, tags=["Facilities"], prefix="/facility")
app.include_router(revisions_router, tags=["Revisions"], prefix="/revision")
app.include_router(weather_router, tags=["Weather"], prefix="/weather")
app.include_router(admin_router, tags=["Admin"], prefix="/admin")


origins = [
    "https://dev.opennem.org.au",
    "https://admin.opennem.org.au",
    "https://admin.opennem.test",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
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
