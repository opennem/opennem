import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.export.controllers import power_week
from opennem.api.export.queries import interconnector_flow_network_regions_query
from opennem.api.time import human_to_interval, human_to_period, valid_database_interval
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.flows import invert_flow_set
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, Station
from opennem.schema.network import (
    NetworkAEMORooftop,
    NetworkAEMORooftopBackfill,
    NetworkAPVI,
    NetworkNEM,
    NetworkNetworkRegion,
    NetworkWEM,
)
from opennem.utils.dates import get_last_completed_interval_for_network, is_aware
from opennem.utils.time import human_to_timedelta

from .controllers import get_balancing_range, get_scada_range, stats_factory
from .queries import (
    emission_factor_region_query,
    energy_facility_query,
    network_fueltech_demand_query,
    network_region_price_query,
    power_facility_query,
)
from .schema import DataQueryResult, OpennemDataSet

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/power/station/{network_code}/{station_code:path}",
    name="Power by Station",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    description="Get the power outputs for a station",
)
def power_station(
    station_code: str = Query(..., description="Station code"),
    network_code: str = Query(..., description="Network code"),
    since: datetime = Query(None, description="Since time"),
    date_min: datetime = Query(None, description="From datetime"),
    date_max: datetime = Query(None, description="To datetime"),
    interval_human: str = Query(None, description="Interval"),
    period_human: str = Query("7d", description="Period"),
    session: Session = Depends(get_database_session),
    engine=Depends(get_database_engine),  # type: ignore
) -> OpennemDataSet:
    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    latest_network_interval = get_last_completed_interval_for_network(network=network)

    # make all times aware
    if since and not is_aware(since):
        since = since.astimezone(network.get_fixed_offset())

    if date_min and not is_aware(date_min):
        date_min = date_min.astimezone(network.get_fixed_offset())

    if date_max and not is_aware(date_max):
        date_max = date_max.astimezone(network.get_fixed_offset())

    if not since:
        since = latest_network_interval - human_to_timedelta("7d")

    if not interval_human:
        # @NOTE rooftop data is 15m
        if station_code.startswith("ROOFTOP"):
            interval_human = "15m"
        else:
            interval_human = f"{network.interval_size}m"

    interval = human_to_interval(interval_human)
    period = human_to_period(period_human)
    units = get_unit("power")

    station: Station | None = (
        session.query(Station)
        .join(Facility)
        .filter(Station.code == station_code)
        .filter(Facility.network_id == network.code)
        .filter(Station.approved.is_(True))
        .one_or_none()
    )

    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    facilities_date_range = station.scada_range

    logger.debug(f"Facilities date range: {facilities_date_range}")

    if not date_max:
        date_max = latest_network_interval

    if not date_min:
        date_min = since

        if facilities_date_range.date_min and date_min < facilities_date_range.date_min:
            date_min = facilities_date_range.date_min

    time_series = OpennemExportSeries(start=date_min, end=date_max, network=network, interval=interval, period=period)

    logger.debug(time_series)

    query = power_facility_query(time_series, station.facility_codes)

    logger.debug(query)

    with engine.connect() as c:
        results = list(c.execute(query))

    stats = [DataQueryResult(interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None) for i in results]

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    result = stats_factory(
        stats,
        code=station_code,
        network=network,
        interval=interval,
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
    name="Energy by Station",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def energy_station(
    engine=Depends(get_database_engine),  # type: ignore
    session: Session = Depends(get_database_session),
    date_min: datetime = Query(None, description="From datetime"),
    date_max: datetime = Query(None, description="To datetime"),
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
            interval = f"{network.interval_size}m"

    interval_obj = human_to_interval(interval)

    if not valid_database_interval(interval_obj):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid interval size")

    if interval_obj.interval < 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interval for energy must be 1 hour or greater",
        )

    period_obj = human_to_period(period)
    units = get_unit("energy")

    station: Station | None = (
        session.query(Station)
        .join(Station.facilities)
        .filter(Station.code == station_code)
        .filter(Facility.network_id == network.code)
        .one_or_none()
    )

    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    if not station.facilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    # Start date
    date_start = station.scada_range.date_min
    date_end = station.scada_range.date_max
    network_range = get_scada_range(network=network)

    if not date_start:
        date_start = network_range.start

    if not date_end:
        date_end = network_range.end

    time_series = OpennemExportSeries(
        start=date_start,
        end=date_end,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    query = energy_facility_query(
        time_series,
        station.facility_codes,
    )

    logger.debug(query)

    with engine.connect() as c:
        row = list(c.execute(query))

    if len(row) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    results_energy = [DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None) for i in row]

    results_market_value = [DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None) for i in row]

    results_emissions = [DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None) for i in row]

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
        code=station_code,
        include_group_code=True,
    )

    stats.append_set(stats_market_value)

    stats_emissions = stats_factory(
        stats=results_emissions,
        units=get_unit("emissions"),
        network=network,
        interval=interval_obj,
        code=station_code,
        include_group_code=True,
    )

    stats.append_set(stats_emissions)

    return stats


"""

Flows endpoints


"""


@router.get(
    "/flow/network/{network_code}",
    name="Interconnector Flow Network",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def power_flows_network_week(
    engine=Depends(get_database_engine),  # type: ignore
    network_code: str = Query(..., description="Network code"),
    month: date = Query(datetime.now().date(), description="Month to query"),
) -> OpennemDataSet | None:
    engine = get_database_engine()

    network = network_from_network_code(network_code)
    interval_obj = network.get_interval()
    period_obj = human_to_period("1M")

    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")

    scada_range = get_scada_range(network=network)

    if not scada_range:
        raise Exception("Require a scada range")

    if not network:
        raise Exception("Network not found")

    time_series = OpennemExportSeries(
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

    if not row:
        raise Exception(f"No results from query: {query}")

    imports = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
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

    network = None

    try:
        network = network_from_network_code(network_code)
    except Exception:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND)

    interval_obj = network.get_interval()
    period_obj = human_to_period("1M")

    scada_range = get_scada_range(network=network)

    if not scada_range:
        raise Exception("Require a scada range")

    if not network:
        raise Exception("Network not found")

    networks = [network]

    if network == NetworkNEM:
        networks.append(NetworkAEMORooftop)
        networks.append(NetworkAEMORooftopBackfill)

    elif network == NetworkWEM:
        networks.append(NetworkAPVI)

    time_series = OpennemExportSeries(
        start=scada_range.start,
        month=month,
        network=network,
        networks=networks,
        interval=interval_obj,
        period=period_obj,
    )

    stat_set = power_week(time_series, network_region_code, include_capacities=True, networks_query=networks)

    if not stat_set:
        raise Exception("No results")

    return stat_set


@router.get(
    "/emissionfactor/network/{network_code}",
    name="Emission Factor per Network Region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def emission_factor_per_network(  # type: ignore
    engine=Depends(get_database_engine),  # type: ignore
    network_code: str = Query(..., description="Network code"),
    interval: str = Query("30m", description="Interval size"),
) -> OpennemDataSet | None:
    engine = get_database_engine()

    network = None

    try:
        network = network_from_network_code(network_code)
    except Exception:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND)

    interval_obj = human_to_interval(interval)

    if not valid_database_interval(interval_obj):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid interval size")

    period_obj = human_to_period("7d")

    if not interval_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid interval size")

    scada_range = get_scada_range(network=network)

    if not scada_range:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find a date range",
        )

    if not network:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Network not found",
        )

    time_series = OpennemExportSeries(
        start=scada_range.start,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    query = emission_factor_region_query(time_series=time_series)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    emission_factors = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        emission_factors,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("emissions_factor"),
        group_field="emission_factor",
        include_group_code=True,
        include_code=True,
    )

    if not result or not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    return result


# @router.get(
#     "/fueltech_mix/{network_code}",
#     name="Fueltech mix by network",
#     response_model=OpennemDataSet,
#     response_model_exclude_unset=True,
# )
def fueltech_demand_mix(
    engine: Engine = Depends(get_database_engine),  # type: ignore
    network_code: str = Query(..., description="Network code"),
) -> OpennemDataSet:
    """Return fueltech proportion of demand for a network

    Args:
        engine ([type], optional): Database engine. Defaults to Depends(get_database_engine).

    Raises:
        HTTPException: No results

    Returns:
        OpennemData: data set

    @TODO optimize this quer
    """
    engine = get_database_engine()

    network = None

    try:
        network = network_from_network_code(network_code)
    except Exception:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND)

    interval_obj = human_to_interval("5m")
    period_obj = human_to_period("1d")

    scada_range = get_scada_range(network=network)

    if not scada_range:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find a date range",
        )

    if not network:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Network not found",
        )

    time_series = OpennemExportSeries(
        start=scada_range.start,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    query = network_fueltech_demand_query(time_series=time_series)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    result_set = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        result_set,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("emissions_factor"),
        group_field="emission_factor",
        include_group_code=True,
        include_code=True,
    )

    if not result or not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    return result


# Price stats endpoints


@router.get(
    "/price/{network_code}/{network_region}",
    name="Price history by network and network region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
@router.get(
    "/price/{network_code}",
    name="Price history by network and network region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
)
def price_network_endpoint(
    engine: Engine = Depends(get_database_engine),
    network_code: str = Path(..., description="Network code"),
    network_region: str | None = Query(None, description="Network region code"),
    forecasts: bool = Query(False, description="Include price forecasts"),
) -> OpennemDataSet:
    """Returns network and network region price info for interval which defaults to network
    interval size

    Args:
        engine ([type], optional): Database engine. Defaults to Depends(get_database_engine).

    Raises:
        HTTPException: No results

    Returns:
        OpennemData: data set
    """
    engine = get_database_engine()

    network = None

    try:
        network = network_from_network_code(network_code)
    except Exception:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND)

    interval_obj = human_to_interval("5m")
    period_obj = human_to_period("1d")

    scada_range = get_balancing_range(network=network, include_forecasts=forecasts)

    if not scada_range:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find a date range",
        )

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found",
        )

    time_series = OpennemExportSeries(
        start=scada_range.start,
        network=network,
        interval=interval_obj,
        period=period_obj,
    )

    if network_region:
        time_series.network.regions = [NetworkNetworkRegion(code=network_region)]

    query = network_region_price_query(time_series=time_series)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    result_set = [DataQueryResult(interval=i[0], result=i[3], group_by=i[2] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        result_set,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("price"),
        group_field="price",
        include_group_code=True,
        include_code=True,
    )

    if not result or not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    return result
