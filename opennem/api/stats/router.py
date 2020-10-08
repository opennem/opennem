from datetime import datetime
from itertools import groupby
from operator import attrgetter

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.core.networks import network_from_network_region
from opennem.core.time import human_to_interval
from opennem.db import get_database_engine, get_database_session
from opennem.db.models.opennem import FacilityScada, Station

from .controllers import stats_factory, stats_set_factory
from .queries import energy_facility, energy_year_network, price_network_region
from .schema import OpennemData, OpennemDataHistory, OpennemDataSet

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


SUPPORTED_PERIODS = ["7D", "1M", "1Y", "ALL"]
SUPPORTED_INTERVALS = ["1d", "1h", "1M"]


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
    interval: str = Query("1d", description="Interval"),
    period: str = Query("7d", description="Period"),
) -> OpennemDataSet:
    """
        Get energy output for a station (list of facilities)
        over a period
    """

    if interval not in SUPPORTED_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interval not supported",
        )

    period = period.upper()

    if period not in SUPPORTED_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not supported",
        )

    network_code = network_code.upper()

    if network_code not in ["WEM", "NEM"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    station = (
        session.query(Station)
        .join(Station.facilities)
        .filter(Station.code == station_code)
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

    result_set = {}

    for (facility_code, trading_interval), record in groupby(
        results, lambda x: (x[1], x[0])
    ):
        trading_interval = str(trading_interval)

        if facility_code not in result_set:
            result_set[facility_code] = {}

        if trading_interval not in result_set[facility_code]:
            result_set[facility_code][trading_interval] = []

        record = list(record).pop()

        result_set[facility_code][trading_interval] = (
            round(float(record[2]), 2) if record[2] else None
        )

    result_output_sets = []

    for facility_code, record in result_set.items():
        dates = list(record.keys())
        start = min(dates)
        end = max(dates)

        history = OpennemDataHistory(
            start=start,
            last=end,
            interval=interval,
            data=list(record.values()),
        )

        data = OpennemData(
            network=network_code,
            data_type="energy",
            units="MWh",
            code=facility_code,
            history=history,
        )

        result_output_sets.append(data)

    output = OpennemDataSet(
        data_type="energy", code=station_code, data=result_output_sets
    )

    return output


@router.get("/energy/network/year/{network_code}", name="Energy Network")
def energy_network(
    engine=Depends(get_database_engine),
    network_code: str = Query(..., description="Network code"),
    year: int = Query(None, description="Year"),
) -> OpennemDataSet:
    query = energy_year_network(year=year, network_code=network_code)

    results = []

    network = network_from_network_region(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Network not found."
        )

    network_timezone = network.get_timezone()

    with engine.connect() as c:
        results = list(c.execute(query))

    if len(results) < 1:
        print(query)
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
    interval: str = Query("1d", description="Interval"),
    period: str = Query("7d", description="Period"),
) -> OpennemData:
    if interval not in SUPPORTED_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interval not supported",
        )

    period = period.upper()

    if period not in SUPPORTED_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not supported",
        )

    network_code = network_code.upper()

    if network_code not in ["WEM", "NEM"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such network",
        )

    query = price_network_region(
        network_code=network_code,
        region_code=region_code,
        interval=interval,
        period=period,
    )

    # print(query)

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
    start = min(dates)
    end = max(dates)

    history = OpennemDataHistory(
        start=start,
        last=end,
        interval=interval,
        data=list(result_set.values()),
    )

    data = OpennemData(
        network=network_code,
        data_type="price",
        units="$ AUD",
        region=region_code,
        code=region_code,
        history=history,
    )

    return data

