import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.time import human_to_interval, human_to_period
from opennem.core.networks import network_from_network_code
from opennem.core.normalizers import normalize_duid
from opennem.core.units import get_unit
from opennem.db import get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, Station
from opennem.schema.time import TimePeriod
from opennem.utils.time import human_to_timedelta

from .controllers import get_scada_range, stats_factory
from .queries import (
    energy_facility_query,
    energy_network,
    energy_network_fueltech,
    energy_network_fueltech_all,
    energy_network_fueltech_year,
    power_facility_query,
    power_network_fueltech,
    price_network_monthly,
    price_network_region,
)
from .schema import DataQueryResult, OpennemDataSet

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/power/unit/{network_code}/{unit_code:path}",
    name="stats:Unit Power",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def power_unit(
    unit_code: str = Query(..., description="Unit code"),
    network_code: str = Query(..., description="Network code"),
    interval_human: str = Query(None, description="Interval"),
    period_human: str = Query("7d", description="Period"),
    engine=Depends(get_database_engine),
) -> OpennemDataSet:

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval_human:
        interval_human = "{}m".format(network.interval_size)

    interval = human_to_interval(interval_human)
    period = human_to_period(period_human)
    units = get_unit("power")

    stats = []

    facility_codes = [normalize_duid(unit_code)]

    query = power_facility_query(
        facility_codes, network.code, interval=interval, period=period
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
            detail="Unit stats not found",
        )

    output = stats_factory(
        stats,
        code=unit_code,
        interval=interval,
        period=period,
        units=units,
        network=network,
    )

    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stats found",
        )

    return output


@router.get(
    "/power/station/{network_code}/{station_code:path}",
    name="stats:Station Power",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def power_station(
    station_code: str = Query(..., description="Station code"),
    network_code: str = Query(..., description="Network code"),
    since: datetime = Query(None, description="Since time"),
    interval_human: str = Query(None, description="Interval"),
    period_human: str = Query("7d", description="Period"),
    session: Session = Depends(get_database_session),
    engine=Depends(get_database_engine),
) -> OpennemDataSet:
    if not since:
        since = datetime.now() - human_to_timedelta("7d")

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval_human:
        # @NOTE rooftop data is 15m
        if station_code.startswith("ROOFTOP"):
            interval_human = "15m"
        else:
            interval_human = "{}m".format(network.interval_size)

    interval = human_to_interval(interval_human)
    period = human_to_period(period_human)
    units = get_unit("power")

    station = (
        session.query(Station)
        .join(Facility)
        .filter(Station.code == station_code)
        .filter(Facility.network_id == network.code)
        .filter(Station.approved.is_(True))
        .one_or_none()
    )

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Station not found"
        )

    facility_codes = list(set([f.code for f in station.facilities]))

    stats = []

    query = power_facility_query(
        facility_codes, network=network, interval=interval, period=period
    )

    logger.debug(query)

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
        period=period,
        include_group_code=True,
        units=units,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results found",
        )

    return result


@router.get(
    "/power/fueltech/{network_code}/{station_code:path}",
    name="stats:Network Fueltech Power",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def power_network_fueltech_api(
    network_code: str = Query(..., description="Network code"),
    network_region: str = Query(None, description="Network region"),
    interval_human: str = Query(None, description="Interval"),
    period_human: str = Query("7d", description="Period"),
    engine=Depends(get_database_engine),
) -> OpennemDataSet:
    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval_human:
        interval_human = "{}m".format(network.interval_size)

    interval = human_to_interval(interval_human)
    period = human_to_period(period_human)
    units = get_unit("power")

    scada_range = get_scada_range(network=network)

    query = power_network_fueltech(
        network=network,
        interval=interval,
        period=period,
        network_region=network_region,
        scada_range=scada_range,
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
        code=network.code,
        network=network,
        interval=interval,
        period=period,
        units=units,
        region=network_region,
        fueltech_group=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results found",
        )

    return result


"""
    Energy endpoints
"""


@router.get(
    "/energy/station/{network_code}/{station_code}",
    name="Energy Station",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval:
        # @NOTE rooftop data is 15m
        if station_code.startswith("ROOFTOP"):
            interval = "15m"
        else:
            interval = "{}m".format(network.interval_size)

    interval_obj = human_to_interval(interval)
    period_obj = human_to_period(period)
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

    query = energy_facility_query(
        facility_codes,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    logger.debug(query)

    with engine.connect() as c:
        row = list(c.execute(query))

    if len(row) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    results_energy = [
        DataQueryResult(
            interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None
        )
        for i in row
    ]

    results_emissions = [
        DataQueryResult(
            interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None
        )
        for i in row
    ]

    # results_emissions = [
    #     DataQueryResult(
    #         interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None
    #     )
    #     for i in row
    # ]

    if len(results_energy) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    stats = stats_factory(
        stats=results_energy,
        units=units,
        network=network,
        interval=interval_obj,
        period=period_obj,
        code=station_code,
    )

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    # stats_market_value = stats_factory(
    #     stats=results_market_value,
    #     units=get_unit("market_value"),
    #     network=network,
    #     interval=interval_obj,
    #     period=period_obj,
    #     code=station_code,
    # )

    # stats.append_set(stats_market_value)

    stats_emissions = stats_factory(
        stats=results_emissions,
        units=get_unit("emissions"),
        network=network,
        interval=interval_obj,
        period=period_obj,
        code=network.code.lower(),
    )

    stats.append_set(stats_emissions)

    return stats


@router.get(
    "/energy/network/{network_code}",
    name="Energy Network",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def energy_network_api(
    engine=Depends(get_database_engine),
    network_code: str = Query(..., description="Network code"),
    interval_human: str = Query("1d", description="Interval"),
    period_human: str = Query("1Y", description="Period"),
) -> OpennemDataSet:

    results = []

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval_human:
        interval_human = "{}m".format(network.interval_size)

    interval = human_to_interval(interval_human)
    period = human_to_period(period_human)
    units = get_unit("energy_giga")

    query = energy_network(network=network, interval=interval, period=period)

    with engine.connect() as c:
        results = list(c.execute(query))

    if len(results) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No results"
        )

    stats = [
        DataQueryResult(
            interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None
        )
        for i in results
    ]

    result = stats_factory(
        stats,
        code=network.code,
        network=network,
        interval=interval,
        period=period,
        units=units,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results found",
        )

    return result


@router.get(
    "/energy/fueltech/{network_code}/{station_code:path}",
    name="stats:Network Fueltech Energy",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def energy_network_fueltech_api(
    network_code: str = Query(None, description="Network code"),
    network_region: str = Query(None, description="Network region"),
    interval_human: str = Query("1d", description="Interval"),
    year: int = Query(None, description="Year to query"),
    period_human: str = Query("1Y", description="Period"),
    engine=Depends(get_database_engine),
) -> OpennemDataSet:
    network = network_from_network_code(network_code)
    interval = human_to_interval(interval_human)

    period_obj: TimePeriod = human_to_period("1Y")

    if period_human:
        period_obj = human_to_period(period_human)

    units = get_unit("energy_giga")

    query = ""

    if year and isinstance(year, int):
        period_obj = human_to_period("1Y")

        if year > datetime.now().year or year < 1996:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Not a valid year",
            )

        scada_range = get_scada_range(network=network)

        query = energy_network_fueltech_year(
            network=network,
            interval=interval,
            year=year,
            network_region=network_region,
            scada_range=scada_range,
        )
    elif period_obj and period_obj.period_human == "all":
        scada_range = get_scada_range(network=network)

        query = energy_network_fueltech_all(
            network=network,
            network_region=network_region,
            scada_range=scada_range,
        )
    else:
        query = energy_network_fueltech(
            network=network,
            interval=interval,
            period=period_obj,
            network_region=network_region,
        )

    # print(query)

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
            detail="Energy stats not found",
        )

    result = stats_factory(
        stats,
        code=network.code,
        network=network,
        interval=interval,
        period=period_obj,
        units=units,
        region=network_region,
        fueltech_group=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No stats"
        )

    return result


"""
    Price endpoints
"""


@router.get(
    "/price/{network_code}/{network_region_code}",
    name="Price Network Region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def price_network_region_api(
    engine=Depends(get_database_engine),
    network_code: str = Query(..., description="Network code"),
    network_region_code: str = Query(..., description="Region code"),
    interval_human: str = Query(None, description="Interval"),
    period_human: str = Query("7d", description="Period"),
    year: Optional[int] = None,
) -> OpennemDataSet:
    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval_human:
        interval_human = "{}m".format(network.interval_size)

    interval = human_to_interval(interval_human)

    period_obj = None

    if period_human:
        period_obj = human_to_period(period_human)

    units = get_unit("price")

    scada_range = get_scada_range(network=network)

    if (
        period_obj
        and period_obj.period_human == "all"
        and interval.interval_human == "1M"
    ):
        query = price_network_monthly(
            network=network,
            network_region_code=network_region_code,
            scada_range=scada_range,
        )
    else:
        query = price_network_region(
            network=network,
            network_region_code=network_region_code,
            interval=interval,
            period=period_obj,
            scada_range=scada_range,
            year=year,
        )

    with engine.connect() as c:
        results = list(c.execute(query))

    if len(results) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No data found"
        )

    stats = [
        DataQueryResult(
            interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None
        )
        for i in results
    ]

    result = stats_factory(
        stats,
        code=network.code,
        region=network_region_code,
        network=network,
        interval=interval,
        period=period_obj,
        units=units,
        group_field="price",
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results found",
        )

    return result
