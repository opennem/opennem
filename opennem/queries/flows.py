""" Flow queries """
import logging
from datetime import datetime
from textwrap import dedent

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.queries.flows")


def get_interconnector_intervals_query(date_start: datetime, date_end: datetime, network: NetworkSchema) -> str:
    """Load interconenctor intervals v1"""
    query = """
        select
            time_bucket_gapfill('5min', fs.trading_interval) as trading_interval,
            f.interconnector_region_from,
            f.interconnector_region_to,
            coalesce(sum(fs.generated), 0) as generated
        from facility_scada fs
        left join facility f
            on fs.facility_code = f.code
        where
            fs.trading_interval >= '{date_start}'
            and fs.trading_interval < '{date_end}'
            and f.interconnector is True
            and f.network_id = '{network_id}'
        group by 1, 2, 3
        order by
            1 asc;

    """.format(
        date_start=date_start,
        date_end=date_end,
        network_id=network.code,
    )

    logger.debug(query)

    return query


def power_network_flow_query(time_series: OpennemExportSeries, network_region: str) -> str:
    """Get interconnector region flows using the aggregate tables"""

    ___query = """
    select
        time_bucket_gapfill('{interval}', nf.trading_interval) as trading_interval,
        nf.network_id,
        nf.network_region,
        max(nf.energy_imports) * {unit_scale} as energy_imports,
        max(nf.energy_exports) * {unit_scale} as energy_exports,
        max(nf.emissions_imports) * {unit_scale} as emission_imports,
        max(nf.emissions_exports) * {unit_scale} as emission_exports,
        max(nf.market_value_imports) * {unit_scale} as market_value_imports,
        max(nf.market_value_exports) * {unit_scale} as market_value_exports,
        case when abs(max(nf.emissions_imports)) > 0
            then
                abs(max(nf.energy_imports)) / abs(max(nf.emissions_imports))
            else 0
        end as intensity_imports,
        case when max(nf.emissions_exports) > 0
            then
                max(nf.energy_exports) / max(nf.emissions_exports)
            else 0
        end as intensity_exports
    from at_network_flows nf
    where
        nf.network_id = '{network_id}' and
        nf.network_region= '{network_region}' and
        nf.trading_interval <= '{date_end}' and
        nf.trading_interval >= '{date_start}'
    group by 1, 2, 3
    order by 1 desc;


    """

    time_series_range = time_series.get_range()
    date_max = time_series_range.end
    date_min = time_series_range.start

    query = ___query.format(
        interval=time_series.interval.interval_sql,
        network_id=time_series.network.code,
        network_region=network_region,
        date_start=date_min,
        date_end=date_max,
        # @NOTE since at_network_flows is calculated as an energy we need to multiple it back out
        unit_scale=12,
    )

    return dedent(query)


def energy_network_flow_query(
    time_series: OpennemExportSeries,
    network_region: str,
    networks_query: list[NetworkSchema] | None = None,
) -> str:
    """
    Get emissions for a network or network + region
    based on a year v1
    """

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
    select
        date_trunc('{trunc}', t.trading_interval) as trading_interval,
        sum(t.imports_energy),
        sum(t.exports_energy),
        abs(sum(t.imports_market_value_rrp)),
        abs(sum(t.exports_market_value_rrp))
    from (
        select
            ei.trading_interval,
            ei.imports_energy,
            ei.exports_energy,
            ei.imports_market_value,
            ei.exports_market_value,
            ei.imports_market_value_rrp,
            ei.exports_market_value_rrp
        from mv_interchange_energy_nem_region ei
        where
            ei.trading_interval <= '{date_max}'
            and ei.trading_interval >= '{date_min}'
            and ei.network_region='{network_region}'
    ) as t
    group by 1
    order by 1 desc
    """

    date_range = time_series.get_range()

    return dedent(
        __query.format(
            network_region=network_region,
            trunc=date_range.interval.trunc,
            date_min=date_range.start,
            date_max=date_range.end,
        )
    )


def energy_network_interconnector_emissions_query(
    time_series: OpennemExportSeries,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> str:
    """
    Get emissions for a network or network + region
    based on a year
    """

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
    select
        t.trading_interval at time zone '{timezone}' as trading_interval,
        t.flow_from,
        t.flow_to,
        t.flow_energy as energy,
        t.flow_from_emissions,
        t.flow_to_emissions
    from vw_region_flow_emissions t
    where
        t.trading_interval <= '{date_max}' and
        t.trading_interval >= '{date_min}' and
        {network_region_query}
        1=1
    order by 1 desc
    """

    timezone = time_series.network.timezone_database
    network_region_query = ""

    # Get the time range using either the old way or the new v4 way
    time_series_range = time_series.get_range()
    date_max = time_series_range.end
    date_min = time_series_range.start

    if network_region:
        network_region_query = f"""
            (t.flow_from='{network_region}' or t.flow_to='{network_region}') and
        """

    return dedent(
        __query.format(
            timezone=timezone,
            # trunc=date_range.interval.trunc,
            date_min=date_min,
            date_max=date_max,
            network_region_query=network_region_query,
        )
    )


def get_network_flows_emissions_market_value_query(
    time_series: OpennemExportSeries, network_region_code: str | None = None
) -> str:
    """Gets the flow energy (in GWh) and the market value (in $) and emissions
    for a given network and network region

    Used in export task controllers and the API

    @TODO abstract scale per opennem.units"""

    __query = """
        select
            date_trunc('{trunc}', t.trading_interval at time zone '{timezone}') as trading_interval,
            t.network_id,
            t.network_region,
            sum(t.imports_energy) / 1000 as imports_energy,
            sum(t.exports_energy) / 1000 as exports_energy,
            abs(sum(t.emissions_imports)) as imports_emissions,
            abs(sum(t.emissions_exports)) as exports_emissions,
            sum(t.market_value_imports) as imports_market_value,
            sum(t.market_value_exports) as exports_market_value,
            case when abs(sum(t.imports_energy)) > 0 then
                sum(t.emissions_imports) / abs(sum(t.imports_energy))
            else 0 end as imports_market_value_rrp,
            case when abs(sum(t.exports_energy)) > 0 then
                sum(t.emissions_exports) / sum(t.exports_energy)
            else 0 end as export_emission_factor
        from (
            select
                time_bucket_gapfill('5 min', t.trading_interval) as trading_interval,
                t.network_id,
                t.network_region,
                coalesce(sum(t.energy_imports), 0) as imports_energy,
                coalesce(sum(t.energy_exports), 0) as exports_energy,
                coalesce(sum(t.emissions_imports), 0) as emissions_imports,
                coalesce(sum(t.emissions_exports), 0) as emissions_exports,
                coalesce(sum(t.market_value_imports), 0) as market_value_imports,
                coalesce(sum(t.market_value_exports), 0) as market_value_exports
            from at_network_flows t
            where
                t.trading_interval < '{date_max}' and
                t.trading_interval >= '{date_min}' and
                t.network_id = '{network_id}' and
                {network_region_query}
            group by 1, 2, 3
        ) as t
        group by 1, 2, 3
        order by 1 desc
    """

    #
    __query_optimized = """
        select
            date_trunc('{trunc}', t.trading_interval at time zone '{timezone}') as trading_interval,
            t.network_id,
            t.network_region,
            coalesce(sum(t.energy_imports), 0) / 1000 as imports_energy,
            coalesce(sum(t.energy_exports), 0) / 1000 as exports_energy,
            coalesce(abs(sum(t.emissions_imports)), 0) as emissions_imports,
            coalesce(abs(sum(t.emissions_exports)), 0) as emissions_exports,
            coalesce(sum(t.market_value_imports), 0) as market_value_imports,
            coalesce(sum(t.market_value_exports), 0) as market_value_exports,
            case when abs(sum(t.energy_imports)) > 0 then
                sum(t.emissions_imports) / abs(sum(t.energy_imports))
            else 0 end as imports_market_value_rrp,
            case when abs(sum(t.energy_exports)) > 0 then
                sum(t.emissions_exports) / sum(t.energy_exports)
            else 0 end as export_emission_factor
        from at_network_flows t
        where
            t.trading_interval < '{date_max}' and
            t.trading_interval >= '{date_min}' and
            t.network_id = '{network_id}' and
            {network_region_query}
        group by 1, 2, 3
        order by 1 desc, 2 asc
    """

    network_region_query = ""

    if network_region_code:
        network_region_query = f"""
            t.network_region = '{network_region_code}'
        """

    date_range = time_series.get_range()

    # if we're bucketing by hour or day then we can use the optimized query
    # @NOTE you can do >= int value here against interval.interval but this is more legible.
    run_optimized = False

    if run_optimized and date_range.interval.trunc.lower() in ["hour", "day", "month", "year"]:
        __query = __query_optimized

    return dedent(
        __query.format(
            timezone=time_series.network.timezone_database,
            trunc=date_range.interval.trunc,
            network_id=time_series.network.code,
            date_min=date_range.start,
            date_max=date_range.end,
            network_region_query=network_region_query,
        )
    )
