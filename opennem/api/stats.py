from collections import UserList
from datetime import datetime
from functools import reduce
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from opennem.db import get_database_session
from opennem.db.models.opennem import Facility, FacilityScada

from .schema import ApiBase

router = APIRouter()


class ScadaInterval(object):
    date: datetime
    value: Optional[float]

    def __init__(self, date: datetime, value: Optional[float] = None):
        self.date = date
        self.value = value


class ScadaReading(ApiBase):
    pass


class ScadaReadingSet(UserList):
    code: str
    data: List[ScadaInterval]


@router.get("/power", name="stats:power")
def stats_power(session: Session = Depends(get_database_session),):
    stats = (
        session.query(FacilityScada)
        # .join(Facility, Facility.code == FacilityScada.facility_code)
        .orderby(FacilityScada.trading_interval).all()
    )

    return stats


@router.get("/power/{station_code}", name="stats:Station Power")
def power_station(
    station_code: str = Query(..., description="Station code"),
    since: datetime = Query(None, description="Since time"),
    session: Session = Depends(get_database_session),
):
    stats = (
        session.query(FacilityScada)
        .filter_by(facility_code=station_code)
        .order_by(FacilityScada.trading_interval)
        .all()
    )

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    def append_data(record, scada):
        record["data"].append([scada.trading_interval, scada.generated])
        return record

    output = reduce(append_data, stats, {"code": station_code, "data": []},)

    # stats = reduce

    return output
