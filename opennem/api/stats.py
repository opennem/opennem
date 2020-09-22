from datetime import datetime
from functools import reduce
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from opennem.core.time import human_to_interval
from opennem.db import get_database_session
from opennem.db.models.opennem import Facility, FacilityScada, Station

from .schema import ApiBase

router = APIRouter()


class ScadaInterval(object):
    date: datetime
    value: Optional[float]

    def __init__(self, date: datetime, value: Optional[float] = None):
        self.date = date
        self.value = value


class ScadaReading(Tuple[datetime, Optional[float]]):
    pass


class UnitScadaReading(BaseModel):
    code: str
    data: List[ScadaReading]


class StationScadaReading(BaseModel):
    code: str
    facilities: Dict[str, UnitScadaReading]


@router.get(
    "/power", name="stats:power",
)
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


@router.get(
    "/power/unit/{unit_code}",
    name="stats:Unit Power",
    response_model=UnitScadaReading,
)
def power_unit(
    unit_code: str = Query(..., description="Unit code"),
    since: datetime = Query(None, description="Since time"),
    session: Session = Depends(get_database_session),
) -> UnitScadaReading:
    if not since:
        since = datetime.now() - human_to_interval("7d")

    stats = (
        session.query(FacilityScada)
        .filter_by(facility_code=unit_code)
        .filter(FacilityScada.trading_interval >= since)
    )

    stats = stats.order_by(FacilityScada.trading_interval).all()

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    def append_data(record, scada):
        record["data"].append((scada.trading_interval, scada.generated))
        return record

    output = reduce(append_data, stats, {"code": unit_code, "data": []},)

    return output


@router.get(
    "/power/station/{station_code}",
    name="stats:Station Power",
    response_model=StationScadaReading,
)
def power_station(
    station_code: str = Query(..., description="Station code"),
    since: datetime = Query(None, description="Since time"),
    session: Session = Depends(get_database_session),
) -> StationScadaReading:
    if not since:
        since = datetime.now() - human_to_interval("7d")

    station = (
        session.query(Station)
        .filter(Station.code == station_code)
        .filter(Station.approved == True)
        .one_or_none()
    )

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Station not found"
        )

    facility_codes = list(set([f.code for f in station.facilities]))

    stats = (
        session.query(FacilityScada)
        .filter(FacilityScada.facility_code.in_(facility_codes))
        .filter(FacilityScada.trading_interval >= since)
    )

    stats = stats.order_by(FacilityScada.trading_interval).all()

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    def append_station_data(record, scada):
        if scada.facility_code not in record["facilities"]:
            record["facilities"][scada.facility_code] = {
                "code": scada.facility_code,
                "data": [],
            }

        record["facilities"][scada.facility_code]["data"].append(
            [scada.trading_interval, scada.generated]
        )

        return record

    output = reduce(
        append_station_data, stats, {"code": station_code, "facilities": {}},
    )

    return output
