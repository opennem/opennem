from typing import List

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.stats.controllers import get_scada_range, stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval, human_to_period
from opennem.api.weather.queries import observation_query
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import get_database_engine, get_database_session
from opennem.db.models.opennem import BomStation
from opennem.utils.timezone import get_fixed_timezone

from .schema import WeatherStation

router = APIRouter()


@router.get(
    "/station",
    description="List of weather stations",
    response_model=List[WeatherStation],
    response_model_exclude_unset=True,
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
    description="Weather station record",
    response_model=WeatherStation,
    response_model_exclude_unset=True,
    response_model_exclude=set(["observations"]),
)
def station_record(
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


@router.get(
    "/station/observation/{station_code}",
    description="Observations from a station",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def station_observations_api(
    station_code: str = Query(None, description="Station code"),
    interval_human: str = Query("15m", description="Interval"),
    period_human: str = Query("7d", description="Period"),
    station_codes: List[str] = [],
    network_code: str = "NEM",
    timezone: str = None,
    offset: str = None,
    year: int = None,
    engine=Depends(get_database_engine),
) -> OpennemDataSet:
    units = get_unit("temperature")

    if not interval_human:
        interval = "15m"

    if not period_human:
        period = "7d"

    network = None

    if network_code:
        network = network_from_network_code(network_code)

    if station_code:
        station_codes = [station_code]

    interval = human_to_interval(interval_human)
    period = human_to_period(period_human)

    if timezone:
        timezone = pytz.timezone(timezone)

    if offset:
        timezone = get_fixed_timezone(offset)

    scada_range = None

    if network:
        scada_range = get_scada_range(network=network)

    query = observation_query(
        station_codes=station_codes,
        interval=interval,
        period=period,
        network=network,
        scada_range=scada_range,
        year=year,
    )

    with engine.connect() as c:
        results = list(c.execute(query))

    stats = [
        DataQueryResult(
            interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None
        )
        for i in results
    ]

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    result = stats_factory(
        stats=stats,
        units=units,
        interval=interval,
        period=period,
        network=network,
        code="bom",
        group_field="temperature",
    )

    return result
