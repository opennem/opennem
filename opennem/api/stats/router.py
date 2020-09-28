from datetime import datetime
from itertools import groupby
from operator import attrgetter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.core.time import human_to_interval
from opennem.db import get_database_session
from opennem.db.models.opennem import FacilityScada, Station

from .controllers import stats_factory, stats_set_factory
from .schema import OpennemData, OpennemDataSet, StationScadaReading

router = APIRouter()


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

    output = stats_factory(stats)

    return output


@router.get(
    "/power/unit/{network_code}/{unit_code:path}",
    name="stats:Unit Power",
    response_model=OpennemData,
)
def power_unit(
    unit_code: str = Query(..., description="Unit code"),
    network_code: str = Query(..., description="Network code"),
    since: str = Query(None, description="Since as human interval"),
    since_dt: datetime = Query(None, description="Since as datetime"),
    session: Session = Depends(get_database_session),
) -> OpennemData:
    if not since:
        since = datetime.now() - human_to_interval("7d")

    network_code = network_code.upper()

    if network_code not in ["WEM", "NEM"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    stats = (
        session.query(FacilityScada)
        .filter_by(facility_code=unit_code)
        .filter_by(network_id=network_code)
        .filter(FacilityScada.trading_interval >= since)
        .order_by(FacilityScada.trading_interval)
        .all()
    )

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    output = stats_factory(stats, code=unit_code)

    return output


@router.get(
    "/power/station/{network_code}/{station_code:path}",
    name="stats:Station Power",
    response_model=OpennemDataSet,
)
def power_station(
    station_code: str = Query(..., description="Station code"),
    network_code: str = Query(..., description="Network code"),
    since: datetime = Query(None, description="Since time"),
    session: Session = Depends(get_database_session),
) -> OpennemDataSet:
    if not since:
        since = datetime.now() - human_to_interval("7d")

    network_code = network_code.upper()

    if network_code not in ["WEM", "NEM"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

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
        .filter(FacilityScada.network_id == network_code)
        .filter(FacilityScada.trading_interval >= since)
        .order_by(FacilityScada.trading_interval)
        .all()
    )

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    stats_sets = {}
    stats_list = []

    for code, record in groupby(stats, attrgetter("facility_code")):
        if code not in stats_sets:
            stats_sets[code] = []

        stats_sets[code] += list(record)

    for code, stats_per_unit in stats_sets.items():
        _statset = stats_factory(stats_per_unit, code=code)
        stats_list.append(_statset)

    output = stats_set_factory(
        stats_list, code=station_code, network=network_code
    )

    return output
