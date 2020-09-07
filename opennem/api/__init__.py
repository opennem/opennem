from typing import List, Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from opennem.controllers.stations import (
    create_station,
    get_station,
    get_stations,
)
from opennem.core.loader import load_data
from opennem.db import db_connect
from opennem.db.models.opennem import Facility, Station
from opennem.importer.registry import registry_import
from opennem.schema.opennem import StationSchema, StationSubmission

app = FastAPI()

origins = [
    "https://admin.opennem.org.au",
    "https://admin.opennem.test",
    "http://localhost",
    "http://localhost:3000",
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

engine = db_connect()
session = sessionmaker(bind=engine, autocommit=False, autoflush=False,)


def get_database_session():
    try:
        s = session()
        yield s
    finally:
        s.close()


@app.get(
    "/stations", response_model=List[StationSchema],
)
def stations(
    db: Session = Depends(get_database_session),
    name: Optional[str] = None,
    limit: Optional[int] = None,
    page: int = 1,
) -> List[StationSchema]:
    stations = registry_import().as_list()
    # stations = load_data("registry.json", True)
    # stations = get_stations(db, name=name, limit=limit, page=page)

    return stations


@app.get("/station/{station_id}")
def station(
    session: Session = Depends(get_database_session), station_id: int = None
):
    return get_station(session, station_id)


@app.post("/station")
def station_create(
    session: Session = Depends(get_database_session),
    station: StationSubmission = None,
):
    return True


@app.get("/revisions")
def revisions() -> List[dict]:
    return {}
