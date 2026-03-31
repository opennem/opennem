import logging
import re
from datetime import timedelta

from opennem import settings
from opennem.api.exceptions import OpennemBaseHttpException, OpenNEMInvalidNetworkRegion
from opennem.api.export.queries import (
    country_stats_query,
    interconnector_flow_network_regions_query,
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
    get_fueltech_power_query_clickhouse,
    get_rooftop_forecast_generation_query,
    get_rooftop_generation_combined_query,
)
from opennem.queries.price import get_network_price_demand_query_analytics
from opennem.schema.network import NetworkAU, NetworkNEM, NetworkSchema
from opennem.schema.stats import StatTypes
from opennem.utils.dates import fmt_clickhouse_dt

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

    # Fueltech generation from ClickHouse
    ch_client = get_clickhouse_client()
    query = get_fueltech_power_query_clickhouse(
        time_series=time_series,
        networks_query=networks_query,
        network_region=network_region_code,
    )
    logger.debug(query)
    row = ch_client.execute(query)

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

    logger.debug(query)

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
        units=get_unit("curtailment_solar_utility"),
        network=time_series.network,
        fueltech_group=False,
        fueltech_code="curtailment_solar_utility",
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

    # Truncate all series to the core generation boundary.
    # Core gen fueltechs (wind, gas, solar_utility, etc.) define the chart edge —
    # demand, price, rooftop, and curtailment must not extend past them.
    _core_gen_exclude = {"solar_rooftop", "imports", "exports", "battery_charging", "pumps"}
    core_gen_lasts = [
        s.history.last
        for s in result.data
        if s.fuel_tech and s.fuel_tech not in _core_gen_exclude and s.data_type == "power" and s.history
    ]

    if core_gen_lasts:
        gen_boundary = max(core_gen_lasts)
        for s in result.data:
            if s.history and s.history.last > gen_boundary:
                interval_delta = s.history.get_interval()
                # count how many slots to trim
                excess = int((s.history.last - gen_boundary) / interval_delta)
                if excess > 0:
                    s.history.data = s.history.data[: len(s.history.data) - excess]
                    s.history.last = gen_boundary

    return result


async def demand_network_region_daily(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:  # sourcery skip: raise-specific-error
    """Gets demand market_value and energy for a network -> network_region"""

    from opennem.queries.demand import network_demand_clickhouse_query

    ch_client = get_clickhouse_client()
    query = network_demand_clickhouse_query(time_series=time_series, network_region=network_region_code, networks_query=networks)

    logger.debug(f"ClickHouse demand query: {query}")
    row = ch_client.execute(str(query))

    if network_region_code:
        results_energy = [DataQueryResult(interval=i[0], group_by=i[2], result=i[3] if len(i) > 3 else None) for i in row]
        results_market_value = [DataQueryResult(interval=i[0], group_by=i[2], result=i[4] if len(i) > 4 else None) for i in row]
    else:
        network_code = time_series.network.code
        results_energy = [DataQueryResult(interval=i[0], group_by=network_code, result=i[2] if len(i) > 2 else None) for i in row]
        results_market_value = [
            DataQueryResult(interval=i[0], group_by=network_code, result=i[3] if len(i) > 3 else None) for i in row
        ]

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
        units=get_unit("curtailment_solar_utility_energy"),
        network=time_series.network,
        fueltech_group=False,
        fueltech_code="curtailment_solar_utility",
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


# --- v4 flow export functions (read from CH market_summary) ---


async def energy_interconnector_flows_and_emissions_v4(
    time_series: OpennemExportSeries, network_region_code: str, include_emission_factor: bool = True
) -> OpennemDataSet | None:
    """v4: reads flow data from CH market_summary instead of PG at_network_flows."""

    ch_client = get_clickhouse_client()
    unit_energy = get_unit("energy_giga")
    unit_emissions = get_unit("emissions")

    date_range = time_series.get_range()

    # Map TimeInterval.trunc to CH truncation function
    # Cast to DateTime to avoid Date/DateTime type mismatch in WHERE clauses
    _ch_trunc_map = {
        "5min": "toStartOfFiveMinute(interval)",
        "hour": "toStartOfHour(interval)",
        "day": "toStartOfDay(interval)",
        "week": "toDateTime(toStartOfWeek(interval))",
        "month": "toDateTime(toStartOfMonth(interval))",
        "quarter": "toDateTime(toStartOfQuarter(interval))",
        "year": "toDateTime(toStartOfYear(interval))",
    }
    time_fn = _ch_trunc_map.get(date_range.interval.trunc, "interval")

    query = f"""
        SELECT
            interval,
            network_region,
            imports_energy,
            exports_energy,
            total_emissions_imports,
            total_emissions_exports,
            total_mv_imports,
            total_mv_exports,
            if(abs(imports_energy) > 0, total_emissions_imports / abs(imports_energy * 1000), 0) as imports_emission_factor,
            if(exports_energy > 0, total_emissions_exports / (exports_energy * 1000), 0) as exports_emission_factor
        FROM (
            SELECT
                {time_fn} as interval,
                network_region,
                coalesce(sum(energy_imports), 0) / 1000 as imports_energy,
                coalesce(sum(energy_exports), 0) / 1000 as exports_energy,
                coalesce(sum(emissions_imports), 0) as total_emissions_imports,
                coalesce(sum(emissions_exports), 0) as total_emissions_exports,
                coalesce(sum(market_value_imports), 0) as total_mv_imports,
                coalesce(sum(market_value_exports), 0) as total_mv_exports
            FROM market_summary FINAL
            WHERE network_id = '{time_series.network.code}'
                AND network_region = '{network_region_code}'
                AND interval >= '{fmt_clickhouse_dt(date_range.start)}'
                AND interval < '{fmt_clickhouse_dt(date_range.end)}'
            GROUP BY 1, 2
        )
        ORDER BY 1 DESC
    """

    row = ch_client.execute(query)

    if not row:
        logger.error(f"No v4 flow results for {time_series.network} {network_region_code}")
        return None

    imports = [DataQueryResult(interval=i[0], group_by="imports", result=i[2]) for i in row]
    exports = [DataQueryResult(interval=i[0], group_by="exports", result=i[3]) for i in row]
    import_emissions = [DataQueryResult(interval=i[0], group_by="imports", result=i[4]) for i in row]
    export_emissions = [DataQueryResult(interval=i[0], group_by="exports", result=i[5]) for i in row]
    import_mv = [DataQueryResult(interval=i[0], group_by="imports", result=i[6]) for i in row]
    export_mv = [DataQueryResult(interval=i[0], group_by="exports", result=i[7]) for i in row]
    import_emission_factor = [DataQueryResult(interval=i[0], group_by="imports", result=i[8]) for i in row]
    export_emission_factor = [DataQueryResult(interval=i[0], group_by="exports", result=i[9]) for i in row]

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
        result_import_ef = stats_factory(
            import_emission_factor,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )
        result.append_set(result_import_ef)

        result_export_ef = stats_factory(
            export_emission_factor,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )
        result.append_set(result_export_ef)

    return result
