from typing import List, Optional

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from opennem.controllers.stations import (
    create_station,
    get_station,
    get_stations,
)
from opennem.db import db_connect
from opennem.db.models.opennem import Facility, Station
from opennem.schema.opennem import StationSchema, StationSubmission

app = FastAPI()

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
    stations = get_stations(db, name=name, limit=limit, page=page)

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
