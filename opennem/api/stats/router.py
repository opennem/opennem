import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.export.controllers import power_week
from opennem.api.export.queries import interconnector_flow_network_regions_query
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.flows import invert_flow_set
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, Station
from opennem.schema.dates import TimeSeries
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
    "/power/station/{network_code}/{station_code:path}",
    name="Station Power",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    description="Get the power outputs for a station",
)
def power_station(
    station_code: str = Query(..., description="Station code"),
    network_code: str = Query(..., description="Network code"),
    since: datetime = Query(None, description="Since time"),
    interval_human: str = Query(None, description="Interval"),
    period_human: str = Query("7d", description="Period"),
    session: Session = Depends(get_database_session),
    engine=Depends(get_database_engine),  # type: ignore
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    # @TODO make both of these methods of Station
    facility_codes = list(set([f.code for f in station.facilities]))
    facilities_first_seen: datetime = min([f.data_first_seen for f in station.facilities])

    stats = []

    time_series = TimeSeries(
        start=facilities_first_seen,
        network=network,
        period=period,
        interval=interval,
    )

    query = power_facility_query(time_series, facility_codes)

    logger.debug(query)

    with engine.connect() as c:
        results = list(c.execute(query))

    stats = [
        DataQueryResult(interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None)
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


"""
    Energy endpoints
"""


@router.get(
    "/energy/station/{network_code}/{station_code:path}",
    name="Energy Station",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def energy_station(
    engine=Depends(get_database_engine),  # type: ignore
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    if len(station.facilities) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    facility_codes = list(set([f.code for f in station.facilities]))
    facilities_first_seen: datetime = min([f.data_first_seen for f in station.facilities])

    time_series = TimeSeries(
        start=facilities_first_seen,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    query = energy_facility_query(
        time_series,
        facility_codes,
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
        DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None)
        for i in row
    ]

    results_market_value = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None)
        for i in row
    ]

    results_emissions = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None)
        for i in row
    ]

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
        include_group_code=True,
    )

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    stats_market_value = stats_factory(
        stats=results_market_value,
        units=get_unit("market_value"),
        network=network,
        interval=interval_obj,
        period=period_obj,
        code=station_code,
        include_group_code=True,
    )

    stats.append_set(stats_market_value)

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


"""

Flows endpoints


"""


@router.get(
    "/flow/network/{network_code}",
    name="Flow Region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def power_flows_network_week(
    engine=Depends(get_database_engine),  # type: ignore
    network_code: str = Query(..., description="Network code"),
    month: date = Query(datetime.now().date(), description="Month to query"),
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    network = network_from_network_code(network_code)
    interval_obj = network.get_interval()
    period_obj = human_to_period("1M")

    scada_range = get_scada_range(network=network)

    if not scada_range:
        raise Exception("Require a scada range")

    if not network:
        raise Exception("Network not found")

    time_series = TimeSeries(
        start=scada_range.start,
        month=month,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    query = interconnector_flow_network_regions_query(time_series=time_series)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if len(row) < 1:
        raise Exception("No results from query: {}".format(query))

    imports = [
        DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None)
        for i in row
    ]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
        period=time_series.period,
        interval=time_series.interval,
        units=get_unit("regional_trade"),
        # fueltech_group=True,
        group_field="power",
        include_group_code=True,
        include_code=True,
    )

    if not result or not result.data:
        raise Exception("No results")

    INVERT_SETS = ["VIC1->NSW1", "VIC1->SA1"]

    inverted_data = []

    for ds in result.data:
        if ds.code in INVERT_SETS:
            ds_inverted = invert_flow_set(ds)
            inverted_data.append(ds_inverted)
        else:
            inverted_data.append(ds)

    result.data = inverted_data

    return result


@router.get(
    "/power/network/fueltech/{network_code}/{network_region_code}",
    name="Power Network Region by Fueltech",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def power_network_region_fueltech(
    network_code: str = Query(..., description="Network code"),
    network_region_code: str = Query(..., description="Network region code"),
    month: date = Query(datetime.now().date(), description="Month to query"),
) -> OpennemDataSet:
    network = network_from_network_code(network_code)
    interval_obj = network.get_interval()
    period_obj = human_to_period("1M")

    scada_range = get_scada_range(network=network)

    if not scada_range:
        raise Exception("Require a scada range")

    if not network:
        raise Exception("Network not found")

    time_series = TimeSeries(
        start=scada_range.start,
        month=month,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    stat_set = power_week(time_series, network_region_code, include_capacities=True)

    if not stat_set:
        raise Exception("No results")

    return stat_set
