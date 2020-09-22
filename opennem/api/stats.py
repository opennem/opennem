from collections import UserList
from datetime import datetime
from functools import reduce
from typing import List, Optional, Tuple

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
def stats_power(
    session: Session = Depends(get_database_session),
    since: datetime = Query(None, description="Since time"),
):
    stats = session.query(FacilityScada)

    if since:
        stats = stats.filter(FacilityScada.trading_interval >= since)

    stats = stats.order_by(FacilityScada.trading_interval).all()

    def append_data(record, scada):
        if scada.facility_code not in record:
            record[scada.facility_code] = {
                "code": scada.facility_code,
                "data": [],
            }

        record[scada.facility_code]["data"].append(
            [scada.trading_interval, scada.generated]
        )

        return record

    output = reduce(append_data, stats, {},)

    return output


@router.get("/power/{unit_code}", name="stats:Unit Power")
def power_station(
    unit_code: str = Query(..., description="Unit code"),
    since: datetime = Query(None, description="Since time"),
    session: Session = Depends(get_database_session),
):
    stats = session.query(FacilityScada).filter_by(facility_code=unit_code)

    if since:
        stats = stats.filter(FacilityScada.trading_interval >= since)

    stats = stats.order_by(FacilityScada.trading_interval).all()

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    def append_data(record, scada):
        record["data"].append([scada.trading_interval, scada.generated])
        return record

    output = reduce(append_data, stats, {"code": unit_code, "data": []},)

    return output
