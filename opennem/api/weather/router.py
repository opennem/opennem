from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.db import get_database_session
from opennem.db.models.opennem import BomObservation, BomStation

from .schema import WeatherObservation, WeatherStation

router = APIRouter()


@router.get(
    "/station",
    description="List of weather stations",
    response_model=List[WeatherStation],
)
def station(
    session: Session = Depends(get_database_session),
) -> List[WeatherStation]:
    """
        Get a list of all stations

    """
    stations = session.query(BomStation).all()

    return stations


@router.get(
    "/station/{station_code}",
    description="List of weather stations",
    response_model=WeatherStation,
)
def station(
    station_code: str = Query(..., description="Station code"),
    session: Session = Depends(get_database_session),
) -> WeatherStation:
    """
        Get a single weather station by code

    """
    station = (
        session.query(BomStation)
        .filter(BomStation.code == station_code)
        .one_or_none()
    )

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No station found"
        )

    return station
