from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from opennem.controllers.stations import (
    create_station,
    get_station,
    get_stations,
)
from opennem.schema import OpennemStationSubmission

app = FastAPI()


@app.get("/stations")
def stations(name: str = None, limit: Optional[int] = None, page: int = 1):
    stations = get_stations(name=name, limit=limit, page=page)

    return {"stations": [i for i in stations]}


@app.get("/station/{station_id}")
def station(station_id: int):
    return get_station(station_id)


@app.post("/station")
def station_create(station: OpennemStationSubmission):
    return True
