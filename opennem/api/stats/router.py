from datetime import datetime
from itertools import groupby
from operator import attrgetter, itemgetter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.time import human_to_interval, human_to_period
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, FacilityScada, Station
from opennem.utils.time import human_to_timedelta
from opennem.utils.timezone import make_aware

from .controllers import stats_factory, stats_set_factory
from .queries import (
    energy_facility,
    energy_year_network,
    power_facility,
    price_network_region,
)
from .schema import (
    DataQueryResult,
    OpennemData,
    OpennemDataHistory,
    OpennemDataSet,
)

router = APIRouter()


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
    interval: str = Query(None, description="Interval"),
    period: str = Query("7d", description="Period"),
    session: Session = Depends(get_database_session),
    engine=Depends(get_database_engine),
) -> OpennemData:
    if not since:
        since = datetime.now() - human_to_timedelta("7d")

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    if not interval:
        interval = "{}m".format(network.interval_size)

    interval = human_to_interval(interval)
    period = human_to_period(period)

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

    output = stats_factory(
        stats, code=unit_code, interval=interval, period=period
    )

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
    interval: str = Query(None, description="Interval"),
    period: str = Query("7d", description="Period"),
    session: Session = Depends(get_database_session),
    engine=Depends(get_database_engine),
) -> OpennemDataSet:
    if not since:
        since = datetime.now() - human_to_timedelta("7d")

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    if not interval:
        # @NOTE rooftop data is 15m
        if station_code.startswith("ROOFTOP"):
            interval = "15m"
        else:
            interval = "{}m".format(network.interval_size)

    interval = human_to_interval(interval)
    period = human_to_period(period)
    units = get_unit("energy")

    station = (
        session.query(Station)
        .join(Facility)
        .filter(Station.code == station_code)
        .filter(Facility.network_id == network.code)
        .filter(Station.approved == True)
        .one_or_none()
    )

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Station not found"
        )

    facility_codes = list(set([f.code for f in station.facilities]))

    stats = []

    query = power_facility(
        facility_codes, network_code, interval=interval, period=period
    )

    with engine.connect() as c:
        results = list(c.execute(query))

    stats = [
        DataQueryResult(
            interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None
        )
        for i in results
    ]

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    result = stats_factory(
        stats,
        code=station_code,
        network=network,
        interval=interval,
        units=units,
    )

    return result


@router.get(
    "/energy/station/{network_code}/{station_code}",
    name="Energy Station",
    response_model=OpennemDataSet,
)
def energy_station(
    engine=Depends(get_database_engine),
    session: Session = Depends(get_database_session),
    network_code: str = Query(..., description="Network code"),
    station_code: str = Query(..., description="Station Code"),
    interval: str = Query(None, description="Interval"),
    period: str = Query("7d", description="Period"),
) -> OpennemDataSet:
    """
        Get energy output for a station (list of facilities)
        over a period
    """

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    if not interval:
        # @NOTE rooftop data is 15m
        if station_code.startswith("ROOFTOP"):
            interval = "15m"
        else:
            interval = "{}m".format(network.interval_size)

    interval = human_to_interval(interval)
    period = human_to_period(period)
    units = get_unit("energy")

    station = (
        session.query(Station)
        .join(Station.facilities)
        .filter(Station.code == station_code)
        .filter(Facility.network_id == network.code)
        .one_or_none()
    )

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Station not found"
        )

    if len(station.facilities) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    facility_codes = list(set([f.code for f in station.facilities]))

    query = energy_facility(
        facility_codes, network_code, interval=interval, period=period
    )

    with engine.connect() as c:
        results = list(c.execute(query))

    stats = [
        DataQueryResult(
            interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None
        )
        for i in results
    ]

    if len(stats) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    result = stats_factory(
        stats,
        code=station_code,
        network=network,
        interval=interval,
        units=units,
    )

    return result


@router.get("/energy/network/year/{network_code}", name="Energy Network")
def energy_network(
    engine=Depends(get_database_engine),
    network_code: str = Query(..., description="Network code"),
    year: int = Query(None, description="Year"),
    interval: str = Query(None, description="Interval"),
    period: str = Query("7d", description="Period"),
) -> OpennemDataSet:
    query = energy_year_network(year=year, network_code=network_code)

    results = []

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    if not interval:
        interval = "{}m".format(network.interval_size)

    interval = human_to_interval(interval)
    period = human_to_period(period)

    with engine.connect() as c:
        results = list(c.execute(query))

    if len(results) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No results"
        )

    stat_groups = {}

    for fueltech, record in groupby(results, attrgetter("fueltech")):
        if fueltech not in stat_groups:
            stat_groups[fueltech] = []

        stat_groups[fueltech] += record

    # history = OpennemDataHistory(
    #     start=start.astimezone(network_timezone),
    #     last=end.astimezone(network_timezone),
    #     interval="{}m".format(str(interval)),
    #     data=list(data_grouped.values()),
    # )

    # data = OpennemData(
    #     network=network,
    #     data_type="power",
    #     units="MW",
    #     code=code,
    #     history=history,
    # )


@router.get(
    "/price/{network_code}/{region_code}",
    name="Price Network Region",
    response_model=OpennemData,
)
def price_region(
    session: Session = Depends(get_database_session),
    engine=Depends(get_database_engine),
    network_code: str = Query(..., description="Network code"),
    region_code: str = Query(..., description="Region code"),
    interval: str = Query(None, description="Interval"),
    period: str = Query("7d", description="Period"),
) -> OpennemData:
    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    if not interval:
        interval = "{}m".format(network.interval_size)

    interval = human_to_interval(interval)
    period = human_to_period(period)
    units = get_unit("price")

    query = price_network_region(
        network_code=network_code,
        region_code=region_code,
        interval=interval,
        period=period,
    )

    with engine.connect() as c:
        results = list(c.execute(query))

    result_set = {}

    if len(results) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No data found"
        )

    for res in results:
        price = res[1]

        if price:
            price = round(price, 2)

        result_set[res[0]] = price

    dates = list(result_set.keys())
    start = make_aware(min(dates), network.get_timezone())
    end = make_aware(max(dates), network.get_timezone())

    history = OpennemDataHistory(
        start=start,
        last=end,
        interval=interval.interval_human,
        data=list(result_set.values()),
    )

    data = OpennemData(
        network=network.code,
        data_type=units.unit_type,
        units=units.unit,
        region=region_code,
        code=region_code,
        history=history,
    )

    return data

