""" Flow queries """
from textwrap import dedent

from opennem.schema.dates import TimeSeries
from opennem.schema.network import NetworkSchema


def energy_network_flow_query(
    time_series: TimeSeries,
    network_region: str,
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
    time_series: TimeSeries,
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
    if time_series.time_range:
        date_max = time_series.time_range.end
        date_min = time_series.time_range.start
    else:
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
