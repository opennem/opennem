import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from fastapi_versionizer import api_version
from sqlalchemy import select
from starlette import status

from opennem import settings
from opennem.api.export.controllers import power_week
from opennem.api.export.queries import interconnector_flow_network_regions_query
from opennem.api.keys import ApiAuthorization, api_protected
from opennem.api.time import human_to_interval, human_to_period, valid_database_interval
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.flows import invert_flow_set
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import db_connect, get_read_session
from opennem.db.models.opennem import Facility
from opennem.queries.emissions import get_emission_factor_region_query
from opennem.queries.energy import get_energy_facility_query
from opennem.queries.price import get_network_region_price_query
from opennem.schema.network import NetworkAEMORooftop, NetworkAEMORooftopBackfill, NetworkAPVI, NetworkNEM, NetworkWEM
from opennem.schema.time import TimePeriod
from opennem.users.schema import OpenNEMRoles
from opennem.utils.dates import get_last_completed_interval_for_network, get_today_nem

from .controllers import get_scada_range, get_scada_range_optimized, stats_factory
from .queries import power_facility_query
from .schema import DataQueryResult, OpennemDataSet

logger = logging.getLogger(__name__)

router = APIRouter()


@api_version(3)
@api_protected()
@router.get(
    "/power/station/{network_code}/{facility_code:path}",
    name="Power by Station",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    description="Get the power outputs for a station",
    include_in_schema=False,
)
@api_protected(roles=[OpenNEMRoles.admin])
async def power_station(
    authorization: ApiAuthorization,
    facility_code: str | None = None,
    network_code: str | None = None,
    interval_human: str | None = None,
    period_human: str | None = None,
    period: str | None = None,  # type: ignore
) -> OpennemDataSet:
    if not network_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No network code")

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval_human:
        # @NOTE rooftop data is 15m
        if facility_code and facility_code.startswith("ROOFTOP"):
            interval_human = "15m"
        else:
            interval_human = f"{network.interval_size}m"

    if not period_human:
        period_human = "1d"

    # @NOTE alias period to period_human for backwards compatibility and address issue #255
    # https://github.com/opennem/opennem/issues/255
    if period:
        period_human = period

    interval = human_to_interval(interval_human)
    period_obj: TimePeriod = human_to_period(period_human)
    units = get_unit("power")

    async with get_read_session() as session:
        facility_lookup: Facility | None = (
            (
                await session.execute(
                    select(Facility)
                    .filter(Facility.code == facility_code)
                    .filter(Facility.network_id == network.code)
                    .filter(Facility.approved.is_(True))
                )
            )
            .scalars()
            .one_or_none()
        )

    if not facility_lookup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    date_min = facility_lookup.scada_range.date_start
    date_max = facility_lookup.scada_range.date_end

    if not date_min or not date_max:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station data range not found")

    logger.debug(f"Facilities date range: {date_min} {date_max}")

    time_series = OpennemExportSeries(start=date_min, end=date_max, network=network, interval=interval, period=period_obj)  # type: ignore

    query = power_facility_query(time_series=time_series, facility_code=facility_code)

    logger.debug(query)

    engine = db_connect()

    async with engine.begin() as c:
        results = list(await c.execute(query))

    stats = [DataQueryResult(interval=i[0], result=i[3], group_by=i[2] if len(i) > 1 else None) for i in results]

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    result = stats_factory(
        stats,
        code=facility_code,
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


@api_version(3)
@router.get(
    "/energy/station/{network_code}/{facility_code:path}",
    name="Energy by Station",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@api_protected(roles=[OpenNEMRoles.admin])
async def energy_station(
    authorization: ApiAuthorization,
    network_code: str,
    facility_code: str,
    interval: str | None = None,
    period: str | None = None,
) -> OpennemDataSet:
    """
    Get energy output for a station (list of facilities)
    over a period
    """
    if not network_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No network code")

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such network",
        )

    if not interval:
        # @NOTE rooftop data is 15m
        if facility_code and facility_code.startswith("ROOFTOP"):
            interval = "15m"
        else:
            interval = "1d"

    interval_obj = human_to_interval(interval)

    if not valid_database_interval(interval_obj):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid interval size")

    if interval_obj.interval < 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interval for energy must be 1 hour or greater",
        )

    if not period:
        period = "7d"

    period_obj = human_to_period(period)
    units = get_unit("energy")

    async with get_read_session() as session:
        # ensure the facility exists
        facility_lookup: Facility | None = (
            (
                await session.execute(
                    select(Facility).filter(Facility.code == facility_code).filter(Facility.network_id == network.code)
                )
            )
            .scalars()
            .one_or_none()
        )

    if not facility_lookup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    if not facility_lookup.units:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    # Start date
    date_start = facility_lookup.scada_range.date_start
    date_end = facility_lookup.scada_range.date_end

    # @NOTE only run get scada range if we don't have a date_min or date_max
    if not date_start or not date_end:
        network_range = get_scada_range_optimized(network=network)

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

    query = get_energy_facility_query(
        time_series=time_series,
        facility_code=facility_code,
    )

    logger.debug(query)

    engine = db_connect()

    async with engine.begin() as connection:
        result = await connection.execute(query)
        row = list(result)

    if len(row) < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station stats not found",
        )

    results_energy = [DataQueryResult(interval=i[0], group_by=i[2], result=i[3] if len(i) > 1 else None) for i in row]

    results_emissions = [DataQueryResult(interval=i[0], group_by=i[2], result=i[4] if len(i) > 1 else None) for i in row]

    results_market_value = [DataQueryResult(interval=i[0], group_by=i[2], result=i[5] if len(i) > 1 else None) for i in row]

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
        code=facility_code,
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
        code=facility_code,
        include_group_code=True,
    )

    stats.append_set(stats_market_value)

    stats_emissions = stats_factory(
        stats=results_emissions,
        units=get_unit("emissions"),
        network=network,
        interval=interval_obj,
        code=facility_code,
        include_group_code=True,
    )

    stats.append_set(stats_emissions)

    return stats


"""

Flows endpoints


"""


@api_version(3)
@router.get(
    "/flow/network/{network_code}/{network_region_code}",
    name="Interconnector Flow Network for network region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@router.get(
    "/flow/network/{network_code}",
    name="Interconnector Flow Network",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@api_protected(roles=[OpenNEMRoles.admin])
async def power_flows_network_week(
    authorization: ApiAuthorization,
    network_code: str,
    network_region_code: str | None = None,
    month: date | None = None,
) -> OpennemDataSet | None:
    """Get the last day of network flow data"""

    engine = db_connect()

    network = network_from_network_code(network_code)

    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")

    interval_obj = network.get_interval()
    period_obj = human_to_period("7d")

    if not network:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network not found")

    if not interval_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interval not found")

    scada_range = await get_scada_range(network=network)

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
        latest=True,
    )

    query = interconnector_flow_network_regions_query(time_series=time_series, network_region=network_region_code)

    async with engine.connect() as c:
        logger.debug(query)
        row = list((await c.execute(query)).all())

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No results")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No results")

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


@api_version(3)
@router.get(
    "/power/network/fueltech/{network_code}/{network_region_code}",
    name="Power Network Region by Fueltech",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@router.get(
    "/power/network/fueltech/{network_code}",
    name="Power Network Region by Fueltech",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@api_protected(roles=[OpenNEMRoles.admin])
async def power_network_region_fueltech(
    authorization: ApiAuthorization,
    network_code: str,
    network_region_code: str | None = None,
    month: date | None = None,
) -> OpennemDataSet | RedirectResponse:
    network = None

    # redirect to static JSONs
    redirect_url_format = "https://data.opennem.org.au/v3/stats/au/{network_code_out}/{network_region_out}power/7d.json"

    if not month:
        month = get_today_nem().date()

    try:
        network = network_from_network_code(network_code)
    except Exception:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND) from None

    if not network:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND) from None

    network_code_out = network.code.upper()
    network_region_out = ""

    if network_region_code:
        network_region_out = network_region_code.upper() + "/"

    # @NOTE if the feature is enabled since this output is static we can redirect to the static JSON
    redirect_to = redirect_url_format.format(
        network_code_out=network_code_out,
        network_region_out=network_region_out,
    )

    if settings.redirect_api_static:
        return RedirectResponse(url=redirect_to, status_code=status.HTTP_302_FOUND)

    interval_obj = network.get_interval()
    period_obj = human_to_period("1M")

    scada_range = await get_scada_range(network=network)

    if not scada_range:
        raise Exception("Require a scada range")

    if not network:
        raise Exception("Network not found")

    if not interval_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interval not found")

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
        interval=interval_obj,
        period=period_obj,
    )

    stat_set = await power_week(time_series, network_region_code, networks_query=networks)

    if not stat_set:
        raise Exception("No results")

    return stat_set


@api_version(3)
@router.get(
    "/emissionfactor/network/{network_code}",
    name="Emission Factor per Network Region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@router.get(
    "/emissionfactor/network/{network_code}/{network_region_code}",
    name="Emission Factor for a Network Region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@api_protected(roles=[OpenNEMRoles.admin])
async def emission_factor_per_network(  # type: ignore
    authorization: ApiAuthorization,
    network_code: str,
    interval: str = "5m",
    network_region_code: str | None = None,
) -> OpennemDataSet | None:
    network = None

    engine = db_connect()

    try:
        network = network_from_network_code(network_code)
    except Exception:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND) from None

    if not network:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND)

    interval_obj = human_to_interval(interval)

    if not valid_database_interval(interval_obj):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid interval size")

    period_obj = human_to_period("1d")

    if period_obj.period > 1440:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid period size. Maximum one day")

    if not interval_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid interval size")

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found",
        )

    if network_region_code and not network.regions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network has no regions",
        )

    if network_region_code and network.regions and network_region_code.upper() not in [i.upper() for i in network.regions]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network region not found",
        )

    last_completed_interval = get_last_completed_interval_for_network(network=network)

    query = get_emission_factor_region_query(
        date_min=last_completed_interval - timedelta(days=1),
        date_max=last_completed_interval,
        network=network,
        network_region_code=network_region_code,
        interval=interval_obj,
    )

    async with engine.connect() as c:
        logger.debug(query)
        row = list((await c.execute(query)).all())

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    emission_factors = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        emission_factors,
        network=network,
        interval=interval_obj,
        units=get_unit("emissions_factor"),
        group_field="emission_factor",
        include_group_code=True,
        include_code=True,
        exclude_nulls=False,
    )

    if not result or not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    return result


# Price stats endpoints


@api_version(3)
@router.get(
    "/price/{network_code}/{network_region_code}",
    name="Price history by network and network region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@router.get(
    "/price/{network_code}",
    name="Price history by network and network region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@router.get(
    "/price/network/{network_code}/{network_region_code}",
    name="Price history by network and network region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@router.get(
    "/price/network/{network_code}",
    name="Price history by network and network region",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
@api_protected(roles=[OpenNEMRoles.admin])
async def price_network_endpoint(
    authorization: ApiAuthorization,
    network_code: str,
    network_region_code: str | None = None,
    forecasts: bool = False,
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

    engine = db_connect()

    try:
        network = network_from_network_code(network_code)
    except Exception:
        raise HTTPException(detail="Network not found", status_code=status.HTTP_404_NOT_FOUND) from None

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found",
        )

    if network_region_code and not network.regions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network has no regions",
        )

    if network_region_code and network.regions and network_region_code.upper() not in [i.upper() for i in network.regions]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network region not found",
        )

    human_to_period("1d")

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found",
        )

    last_completed_interval = get_last_completed_interval_for_network(network=network)

    if not network.get_interval():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network has no interval",
        )

    query = get_network_region_price_query(
        date_min=last_completed_interval - timedelta(days=1),
        date_max=last_completed_interval,
        interval=network.get_interval(),
        network=network,
        network_region_code=network_region_code,
        forecast=forecasts,
    )

    async with engine.begin() as c:
        logger.debug(query)
        row = list((await c.execute(query)).all())

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    result_set = [DataQueryResult(interval=i[0], result=i[3], group_by=i[2] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        result_set,
        network=network,
        interval=network.get_interval(),
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
