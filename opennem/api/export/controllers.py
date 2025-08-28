import logging
import re
from datetime import timedelta

from opennem import settings
from opennem.api.exceptions import OpennemBaseHttpException, OpenNEMInvalidNetworkRegion
from opennem.api.export.queries import (
    country_stats_query,
    demand_network_region_query,
    interconnector_flow_network_regions_query,
    interconnector_power_flow,
    power_and_emissions_network_fueltech_query,
    power_network_interconnector_emissions_query,
    price_network_query,
)
from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.units import get_unit
from opennem.db import db_connect, get_database_engine
from opennem.db.clickhouse import get_clickhouse_client
from opennem.queries.curtailment import get_network_curtailment_energy_query_analytics
from opennem.queries.flows import get_network_flows_emissions_market_value_query
from opennem.queries.power import (
    get_fueltech_generation_query,
    get_rooftop_forecast_generation_query,
    get_rooftop_generation_combined_query,
)
from opennem.queries.price import get_network_price_demand_query_analytics
from opennem.schema.network import NetworkAU, NetworkNEM, NetworkSchema
from opennem.schema.stats import StatTypes

_valid_region = re.compile(r"^\w{1,4}\d?$")


logger = logging.getLogger(__name__)


class NoResults(OpennemBaseHttpException):
    detail = "No results"


async def gov_stats_cpi() -> OpennemDataSet | None:
    engine = get_database_engine()

    query = country_stats_query(StatTypes.CPI)

    async with engine.begin() as conn:
        logger.debug(query)
        result = await conn.execute(query)
        row = result.fetchall()

    stats = [DataQueryResult(interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None) for i in row]

    if len(stats) < 1:
        logger.error("No results for gov_stats_cpi returing blank set")
        return None

    result = stats_factory(
        stats,
        code="au.cpi",
        network=NetworkNEM,
        interval=human_to_interval("1Q"),
        units=get_unit("cpi"),
        group_field="gov",
    )

    return result


async def power_flows_region_week(
    time_series: OpennemExportSeries,
    network_region_code: str,
) -> OpennemDataSet | None:
    """Gets the power flows for the most recent week for a region. Used in export_power for the JSON export sets

    from old flows
    """
    engine = get_database_engine()
    unit_power = get_unit("power")

    query = interconnector_power_flow(
        time_series=time_series,
        network_region=network_region_code,
    )

    async with engine.begin() as conn:
        logger.debug(query)
        result = await conn.execute(query)
        rows = result.fetchall()

    if not rows:
        logger.error(f"No results from interconnector_power_flow query for {time_series.interval}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[2], group_by="imports" if len(i) > 1 else None) for i in rows]
    exports = [DataQueryResult(interval=i[0], result=i[3], group_by="exports" if len(i) > 1 else None) for i in rows]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        logger.error(f"No results from interconnector_power_flow stats facoty for {time_series}")
        return None

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    return result


async def network_flows_for_region(
    time_series: OpennemExportSeries,
    network_region_code: str,
    include_emissions: bool = False,
    include_emission_factors: bool = False,
) -> OpennemDataSet | None:
    "Network flows with optional emissions for a region. Up to last_complete_day"

    engine = get_database_engine()
    unit_power = get_unit("power")

    query = power_network_interconnector_emissions_query(
        time_series=time_series,
        network_region=network_region_code,
    )

    async with engine.begin() as conn:
        logger.debug(query)
        result = await conn.execute(query)
        rows = result.fetchall()

    if not rows:
        logger.error(f"No results from interconnector_power_flow query for {time_series.interval}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[1], group_by="imports" if len(i) > 1 else None) for i in rows]
    exports = [DataQueryResult(interval=i[0], result=i[2], group_by="exports" if len(i) > 1 else None) for i in rows]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        logger.error(f"No results from interconnector_power_flow stats facoty for {time_series}")
        return None

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    if include_emissions:
        unit_emissions = get_unit("emissions")

        import_emissions = [DataQueryResult(interval=i[0], group_by="imports", result=i[3]) for i in rows]
        export_emissions = [DataQueryResult(interval=i[0], group_by="exports", result=i[4]) for i in rows]

        result_import_emissions = stats_factory(
            import_emissions,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_import_emissions)

        result_export_emissions = stats_factory(
            export_emissions,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_export_emissions)

    if include_emission_factors:
        unit_emissions_factor = get_unit("emissions_factor")

        # import factors
        import_emissions_factors = [DataQueryResult(interval=i[0], group_by="imports", result=i[7]) for i in rows]
        result_import_emissions_factors = stats_factory(
            import_emissions_factors,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions_factor,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_import_emissions_factors)

        # export factors
        export_emissions_factors = [DataQueryResult(interval=i[0], group_by="exports", result=i[8]) for i in rows]
        result_export_emissions = stats_factory(
            export_emissions_factors,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions_factor,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_export_emissions)

    return result


async def power_flows_network_week(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
) -> OpennemDataSet | None:
    engine = get_database_engine()

    query = interconnector_flow_network_regions_query(time_series=time_series, network_region=network_region_code)

    logging.info(query)

    async with engine.begin() as conn:
        logger.debug(query)
        result = await conn.execute(query)
        row = result.fetchall()

    if not row:
        logger.warning(f"No results from interconnector_flow_network_regions_query with {time_series}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("regional_trade"),
        fueltech_group=True,
        group_field="power",
        include_group_code=True,
    )

    if not result:
        logger.error(f"No results from interconnector_flow_network_regions_query with {time_series}")
        return None

    return result


async def power_week(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:  # sourcery skip: use-fstring-for-formatting
    engine = db_connect()

    if network_region_code and not re.match(_valid_region, network_region_code):
        raise OpenNEMInvalidNetworkRegion()

    query = get_fueltech_generation_query(
        time_series=time_series,
        networks_query=networks_query,
        network_region=network_region_code,
    )

    logger.debug(query)

    async with engine.begin() as conn:
        result = await conn.execute(query)
        row = result.fetchall()

    stats = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    if not stats:
        logger.error(f"No results from power week query with {time_series}")
        return None

    result = stats_factory(
        stats,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
        include_code=True,
    )

    if not result:
        logger.error(f"No results from power week status factory with {time_series}")
        return None

    # emissions
    emissions = [DataQueryResult(interval=i[0], result=i[3], group_by=i[1] if len(i) > 1 else None) for i in row]

    stats_emissions = stats_factory(
        emissions,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("emissions"),
        region=network_region_code,
        fueltech_group=True,
        include_code=True,
    )

    result.append_set(stats_emissions)

    # emission factors
    if settings.show_emission_factors_in_power_outputs:
        emission_factors = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]
        stats_emission_factors = stats_factory(
            emission_factors,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            include_code=True,
        )

        result.append_set(stats_emission_factors)

    # rooftop solar
    query = get_rooftop_generation_combined_query(
        network=time_series.network,
        date_start=time_series.get_range().start,
        date_end=time_series.end,
        network_region=network_region_code,
    )

    async with engine.begin() as conn:
        logger.debug(query)
        result_rooftop = await conn.execute(query)
        row = result_rooftop.fetchall()

    rooftop_generation = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    result_rooftop = stats_factory(
        rooftop_generation,
        network=time_series.network,
        # @NOTE dirty dirty hack to get APVI and AEMO_ROOFTOP to match the 30min interval
        interval=time_series.interval if time_series.network != NetworkAU else human_to_interval("30m"),
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
        cast_nulls=True,
        include_code=True,
    )

    # rooftop forecast
    query = get_rooftop_forecast_generation_query(
        network=time_series.network,
        date_start=time_series.get_range().end,
        date_end=time_series.get_range().end + timedelta(days=1),
        network_region=network_region_code,
    )

    async with engine.begin() as conn:
        logger.debug(query)
        result_rooftop_forecast = await conn.execute(query)
        row = result_rooftop_forecast.fetchall()

    rooftop_forecast_generation = [
        DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row
    ]

    result_rooftop_forecast = stats_factory(
        rooftop_forecast_generation,
        network=time_series.network,
        # @NOTE dirty dirty hack to get APVI and AEMO_ROOFTOP to match the 30min interval
        interval=time_series.interval if time_series.network != NetworkAU else human_to_interval("30m"),
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
        cast_nulls=True,
    )

    # insert the forecast data into the rooftop forecast set
    if result_rooftop and result_rooftop_forecast:
        if (
            hasattr(result_rooftop, "data")
            and len(result_rooftop.data) > 0
            and result_rooftop_forecast.data
            and len(result_rooftop_forecast.data) > 0
        ):
            result_rooftop.data[0].forecast = result_rooftop_forecast.data[0].history

    result.append_set(result_rooftop)

    # price

    query: str = get_network_price_demand_query_analytics(
        network=time_series.network,
        date_min=time_series.get_range().start,
        date_max=time_series.get_range().end,
        network_region_code=network_region_code,
    )

    ch_client = get_clickhouse_client()

    result_price_and_demand_and_curtailment = ch_client.execute(query)

    stats_price_results = [
        DataQueryResult(interval=i[0], result=i[3], group_by=i[1] if len(i) > 1 else None)
        for i in result_price_and_demand_and_curtailment
    ]

    stats_price = stats_factory(
        stats=stats_price_results,
        units=get_unit("price_energy_mega"),
        network=time_series.network,
        interval=time_series.interval,
        region=network_region_code.lower() if network_region_code else None,
        include_code=False,
    )

    result.append_set(stats_price)

    #  demand
    stats_demand_results = [
        DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None)
        for i in result_price_and_demand_and_curtailment
    ]

    stats_demand = stats_factory(
        stats=stats_demand_results,
        units=get_unit("demand"),
        network=time_series.network,
        interval=time_series.interval,
        region=network_region_code,
    )

    result.append_set(stats_demand)

    # curtailment

    # curtailment total

    # stats_curtailment_results = [
    #     DataQueryResult(interval=i[0], result=i[6], group_by=i[1] if len(i) > 1 else None)
    #     for i in result_price_and_demand_and_curtailment
    # ]

    # stats_curtailment = stats_factory(
    #     stats=stats_curtailment_results,
    #     units=get_unit("curtailment"),
    #     network=time_series.network,
    #     interval=time_series.interval,
    #     region=network_region_code,
    # )

    # result.append_set(stats_curtailment)

    stats_curtailment_solar_results = [
        DataQueryResult(interval=i[0], result=i[7], group_by=i[1] if len(i) > 1 else None)
        for i in result_price_and_demand_and_curtailment
    ]

    stats_curtailment_solar = stats_factory(
        stats=stats_curtailment_solar_results,
        units=get_unit("curtailment_solar"),
        network=time_series.network,
        fueltech_group=False,
        fueltech_code="curtailment_solar",
        interval=time_series.interval,
        region=network_region_code,
    )

    result.append_set(stats_curtailment_solar)

    stats_curtailment_wind_results = [
        DataQueryResult(interval=i[0], result=i[8], group_by=i[1] if len(i) > 1 else None)
        for i in result_price_and_demand_and_curtailment
    ]

    stats_curtailment_wind = stats_factory(
        stats=stats_curtailment_wind_results,
        units=get_unit("curtailment_wind"),
        network=time_series.network,
        fueltech_group=False,
        fueltech_code="curtailment_wind",
        interval=time_series.interval,
        region=network_region_code,
    )

    result.append_set(stats_curtailment_wind)

    return result


async def price_for_network_interval(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:
    """Returns price per interval for a network or network region"""
    engine = get_database_engine()

    query = price_network_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    with engine.begin() as conn:
        logger.debug(query)
        result = await conn.execute(query)
        row = result.fetchall()

    price_data = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    price_set = stats_factory(
        stats=price_data,
        code=network_region_code or time_series.network.code.lower(),
        units=get_unit("price"),
        network=time_series.network,
        interval=time_series.interval,
        region=network_region_code,
    )

    return price_set


def power_and_emissions_for_network_interval(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    include_emission_factors: bool = False,
) -> OpennemDataSet | None:
    engine = get_database_engine()

    if network_region_code and not re.match(_valid_region, network_region_code):
        raise OpenNEMInvalidNetworkRegion()

    query = power_and_emissions_network_fueltech_query(
        time_series=time_series,
        network_region=network_region_code,
    )

    with engine.begin() as c:
        logger.debug(query)
        row = list(c.execute(query))

    power_stats = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]
    emission_stats = [DataQueryResult(interval=i[0], result=i[3], group_by=i[1] if len(i) > 1 else None) for i in row]

    if not power_stats:
        logger.error(f"No results from emissions_for_network_interval query with {time_series}")
        return None

    power_result = stats_factory(
        power_stats,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
    )

    if not power_result:
        raise Exception(
            f"No power results for {time_series.network.code} in region {network_region_code} and date \
                range {time_series.get_range().start} => {time_series.get_range().end}"
        )

    emissions_result = stats_factory(
        emission_stats,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("emissions"),
        region=network_region_code,
        fueltech_group=True,
    )

    if emissions_result:
        power_result.append_set(emissions_result)

    if include_emission_factors:
        emission_factor_unit = get_unit("emissions_factor")

        emission_factor_results = [
            DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row
        ]

        emission_factor_set = stats_factory(
            emission_factor_results,
            network=time_series.network,
            interval=time_series.interval,
            units=emission_factor_unit,
            region=network_region_code,
            fueltech_group=True,
        )
        power_result.append_set(emission_factor_set)

    return power_result


async def demand_network_region_daily(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:  # sourcery skip: raise-specific-error
    """Gets demand market_value and energy for a network -> network_region"""

    # Check if we should use ClickHouse for demand data
    if settings.demand_from_market_summary:
        # Use ClickHouse market_summary table
        from opennem.queries.demand import network_demand_clickhouse_query

        ch_client = get_clickhouse_client()
        query = network_demand_clickhouse_query(
            time_series=time_series, network_region=network_region_code, networks_query=networks
        )

        logger.debug(f"Using ClickHouse for demand query: {query}")
        row = ch_client.execute(str(query))

        # ClickHouse returns different column structure depending on whether network_region is included
        if network_region_code:
            # With region: (interval, network_id, network_region, demand_energy, demand_market_value)
            results_energy = [DataQueryResult(interval=i[0], group_by=i[2], result=i[3] if len(i) > 3 else None) for i in row]
            results_market_value = [
                DataQueryResult(interval=i[0], group_by=i[2], result=i[4] if len(i) > 4 else None) for i in row
            ]
        else:
            # Without region: (interval, network_id, demand_energy, demand_market_value)
            # Use network_id as group_by for consistency
            results_energy = [DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 2 else None) for i in row]
            results_market_value = [
                DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 3 else None) for i in row
            ]
    else:
        # Use PostgreSQL at_network_demand table (existing behavior)
        engine = get_database_engine()
        query = demand_network_region_query(time_series=time_series, network_region=network_region_code, networks=networks)

        async with engine.begin() as conn:
            logger.debug(query)
            result = await conn.execute(query)
            row = result.fetchall()

        results_energy = [DataQueryResult(interval=i[0], group_by=i[2], result=i[3] if len(i) > 1 else None) for i in row]
        results_market_value = [DataQueryResult(interval=i[0], group_by=i[2], result=i[4] if len(i) > 1 else None) for i in row]

    if not results_energy:
        logger.error(f"No results from query: {query}")
        return None

    # demand based values for VWP
    stats = stats_factory(
        stats=results_energy,
        units=get_unit("demand.energy_giga"),
        network=time_series.network,
        fueltech_group=False,
        interval=time_series.interval,
        region=network_region_code,
    )

    if not stats:
        raise Exception(f"Not stats for demand_network_region_daily: {network_region_code}")

    if stats_market_value := stats_factory(
        stats=results_market_value,
        units=get_unit("demand.market_value"),
        network=time_series.network,
        fueltech_group=False,
        interval=time_series.interval,
        code=time_series.network.code.lower(),
        region=network_region_code,
    ):
        stats.append_set(stats_market_value)

    return stats


async def curtailment_network_region_daily(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:  # sourcery skip: raise-specific-error
    """Gets demand market_value and energy for a network -> network_region"""
    ch_client = get_clickhouse_client()

    query = get_network_curtailment_energy_query_analytics(
        network=time_series.network,
        interval=time_series.interval,
        date_min=time_series.get_range().start,
        date_max=time_series.get_range().end,
        network_region_code=network_region_code,
    )

    result_curtailment = ch_client.execute(query)

    result_curtailment_solar = [
        DataQueryResult(interval=i[0], group_by=i[2], result=i[4] if len(i) > 1 else None) for i in result_curtailment
    ]

    result_curtailment_wind = [
        DataQueryResult(interval=i[0], group_by=i[2], result=i[5] if len(i) > 1 else None) for i in result_curtailment
    ]

    if not result_curtailment_solar:
        logger.error(f"No results from query: {query}")
        return None

    stats = OpennemDataSet()

    # curtailment based values for VWP
    if stats_curtailment_solar := stats_factory(
        stats=result_curtailment_solar,
        units=get_unit("curtailment_solar_energy"),
        network=time_series.network,
        fueltech_group=False,
        fueltech_code="curtailment_solar",
        interval=time_series.interval,
        region=network_region_code,
    ):
        stats.append_set(stats_curtailment_solar)

    if stats_curtailment_wind := stats_factory(
        stats=result_curtailment_wind,
        units=get_unit("curtailment_wind_energy"),
        network=time_series.network,
        fueltech_group=False,
        fueltech_code="curtailment_wind",
        interval=time_series.interval,
        code=time_series.network.code.lower(),
        region=network_region_code,
    ):
        stats.append_set(stats_curtailment_wind)

    return stats


async def energy_interconnector_flows_and_emissions_v2(
    time_series: OpennemExportSeries, network_region_code: str, include_emission_factor: bool = True
) -> OpennemDataSet | None:
    engine = get_database_engine()
    unit_energy = get_unit("energy_giga")
    unit_emissions = get_unit("emissions")

    query = get_network_flows_emissions_market_value_query(time_series=time_series, network_region_code=network_region_code)

    async with engine.begin() as conn:
        logger.debug(query)
        result = await conn.execute(query)
        row = result.fetchall()

    if not row:
        logger.error(
            f"No results from energy_interconnector_flows_and_emissions for {time_series.network} "
            "{network_region_code} and {time_series.start} => {time_series.end}"
        )
        return None

    imports = [DataQueryResult(interval=i[0], group_by="imports", result=i[3]) for i in row]
    exports = [DataQueryResult(interval=i[0], group_by="exports", result=i[4]) for i in row]

    import_emissions = [DataQueryResult(interval=i[0], group_by="imports", result=i[5]) for i in row]
    export_emissions = [DataQueryResult(interval=i[0], group_by="exports", result=i[6]) for i in row]

    import_mv = [DataQueryResult(interval=i[0], group_by="imports", result=i[7]) for i in row]
    export_mv = [DataQueryResult(interval=i[0], group_by="exports", result=i[8]) for i in row]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_energy,
        region=network_region_code,
        fueltech_group=True,
    )

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_energy,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    result_import_emissions = stats_factory(
        import_emissions,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_emissions,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_import_emissions)

    result_export_emissions = stats_factory(
        export_emissions,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_emissions,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_export_emissions)

    # market value for flows

    result_import_mv = stats_factory(
        import_mv,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("market_value"),
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_import_mv)

    result_export_mv = stats_factory(
        export_mv,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("market_value"),
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_export_mv)

    if include_emission_factor:
        import_emission_factor = [DataQueryResult(interval=i[0], group_by="imports", result=i[9]) for i in row]
        export_emission_factor = [DataQueryResult(interval=i[0], group_by="exports", result=i[10]) for i in row]

        result_import_emission_factor = stats_factory(
            import_emission_factor,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_import_emission_factor)

        result_export_emission_factor = stats_factory(
            export_emission_factor,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_export_emission_factor)

    return result
