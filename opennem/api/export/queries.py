from datetime import timedelta
from textwrap import dedent
from typing import List, Optional

from sqlalchemy import sql
from sqlalchemy.sql.elements import TextClause

from opennem.api.stats.controllers import networks_to_in
from opennem.schema.dates import TimeSeries
from opennem.schema.network import NetworkAPVI, NetworkNEM, NetworkSchema, NetworkWEM
from opennem.schema.stats import StatTypes


def weather_observation_query(time_series: TimeSeries, station_codes: List[str]) -> str:

    if time_series.interval.interval >= 1440:
        # @TODO replace with mv
        __query = """
        select
            date_trunc('{trunc}', t.observation_hour at time zone '{tz}') as observation_time,
            t.station_id,
            avg(t.temp_avg),
            min(t.temp_min),
            max(t.temp_max)
        from (
            select
                time_bucket_gapfill('1 hour', observation_time) as observation_hour,
                fs.station_id,

                case
                    when avg(fs.temp_air) is not null
                        then avg(fs.temp_air)
                    when max(fs.temp_max) is not null and max(fs.temp_min) is not null
                        then ((max(fs.temp_max) + min(fs.temp_min)) / 2)
                    else NULL
                end as temp_avg,

                case when min(fs.temp_min) is not null
                    then min(fs.temp_min)
                    else min(fs.temp_air)
                end as temp_min,

                case when max(fs.temp_max) is not null
                    then max(fs.temp_max)
                    else max(fs.temp_air)
                end as temp_max

            from bom_observation fs
            where
                fs.station_id in ({station_codes}) and
                fs.observation_time <= '{date_end}' and
                fs.observation_time >= '{date_start}'
            group by 1, 2
        ) as t
        group by 1, 2
        order by 1 asc;
        """.format(
            trunc=time_series.interval.trunc,
            tz=time_series.network.timezone_database,
            station_codes=",".join(["'{}'".format(i) for i in station_codes]),
            date_start=time_series.get_range().start,
            date_end=time_series.get_range().end,
        )

    else:
        __query = """
        select
            time_bucket_gapfill('30 minutes', fs.observation_time) as ot,
            fs.station_id as station_id,

            case when min(fs.temp_air) is not null
                then avg(fs.temp_air)
                else NULL
            end as temp_air,

            case when min(fs.temp_min) is not null
                then min(fs.temp_min)
                else min(fs.temp_air)
            end as temp_min,

            case when max(fs.temp_max) is not null
                then max(fs.temp_max)
                else max(fs.temp_air)
            end as temp_max

        from bom_observation fs
        where
            fs.station_id in ({station_codes}) and
            fs.observation_time <= '{date_end}' and
            fs.observation_time >= '{date_start}'
        group by 1, 2
        order by 1 desc;
        """.format(
            station_codes=",".join(["'{}'".format(i) for i in station_codes]),
            date_start=time_series.get_range().start,
            date_end=time_series.get_range().end,
        )

    return dedent(__query)


def interconnector_power_flow(time_series: TimeSeries, network_region: str) -> str:
    """Get interconnector region flows using materialized view"""

    ___query = """
    select
        time_bucket_gapfill(INTERVAL '5 minutes', bs.trading_interval) as trading_interval,
        bs.network_region,
        case when max(bs.net_interchange) < 0 then
            max(bs.net_interchange)
        else 0
        end as imports,
        case when max(bs.net_interchange) > 0 then
            max(bs.net_interchange)
        else 0
        end as exports
    from balancing_summary bs
    where
        bs.network_id = '{network_id}' and
        bs.network_region= '{region}' and
        bs.trading_interval <= '{date_end}' and
        bs.trading_interval >= '{date_start}'
    group by 1, 2
    order by trading_interval desc;


    """.format(
        network_id=time_series.network.code,
        region=network_region,
        date_start=time_series.get_range().start,
        date_end=time_series.get_range().end,
    )

    return dedent(___query)


def interconnector_flow_network_regions_query(
    time_series: TimeSeries, network_region: Optional[str] = None
) -> str:
    """ """

    __query = """
    select
        fs.trading_interval at time zone '{timezone}' as trading_interval,
        f.network_region || '->' || f.interconnector_region_to as flow_region,
        f.network_region,
        f.interconnector_region_to,
        sum(fs.generated) as flow_power
    from facility_scada fs
    left join facility f on fs.facility_code = f.code
    where
        f.interconnector is True
        and f.network_id='{network_id}'
        and fs.trading_interval <= '{date_end}'
        and fs.trading_interval >= '{date_start}'
        {region_query}
    group by 1, 2, 3, 4
    order by
        1 desc,
        2 asc
    """

    region_query = ""

    if network_region:
        region_query = f"and f.network_region='{network_region}'"

    query = __query.format(
        timezone=time_series.network.timezone_database,
        network_id=time_series.network.code,
        region_query=region_query,
        date_start=time_series.get_range().start,
        date_end=time_series.get_range().end,
    )

    return dedent(query)


def country_stats_query(stat_type: StatTypes, country: str = "au") -> TextClause:
    __query = sql.text(
        dedent(
            """
                select
                    s.stat_date,
                    s.value,
                    s.stat_type
                from stats s
                where s.stat_type = :stat_type and s.country= :country
                order by s.stat_date desc
           """
        )
    ).bindparams(
        stat_type=str(stat_type),
        country=country,
    )

    return __query


def price_network_query(
    time_series: TimeSeries,
    group_field: str = "bs.network_id",
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
        select
            time_bucket_gapfill('{trunc}', bs.trading_interval) as trading_interval,
            {group_field},
            avg(bs.price) as price
        from balancing_summary bs
        where
            bs.trading_interval <= '{date_max}' and
            bs.trading_interval >= '{date_min}' and
            {network_query}
            {network_region_query}
            1=1
        group by 1, 2
        order by 1 desc
    """

    timezone = time_series.network.timezone_database
    network_region_query = ""

    if network_region:
        network_region_query = f"bs.network_region='{network_region}' and "
        group_field = "bs.network_region"

    network_query = "bs.network_id IN ({}) and ".format(networks_to_in(networks_query))

    if len(networks_query) > 1:
        group_field = "'AU'"

    date_max = time_series.get_range().end
    date_min = time_series.get_range().start

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=time_series.interval.interval_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            group_field=group_field,
        )
    )

    return query


def network_demand_query(
    time_series: TimeSeries,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:
    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
    select
        trading_interval at time zone '{timezone}',
        network_id,
        max(demand_total) as demand
    from balancing_summary bs
    where
        bs.trading_interval <= '{date_max}' and
        bs.trading_interval >= '{date_min}' and
        {network_query}
        {network_region_query}
        1=1
    group by
        1, {groups_additional}
    order by 1 desc;
    """

    group_keys = ["network_id"]
    network_region_query = ""

    if network_region:
        group_keys.append("network_region")
        network_region_query = f"bs.network_region = '{network_region}' and "

    groups_additional = ", ".join(group_keys)

    network_query = "bs.network_id IN ({}) and ".format(networks_to_in(networks_query))

    date_max = time_series.get_range().end
    date_min = time_series.get_range().start

    query = __query.format(
        timezone=time_series.network.timezone_database,
        date_max=date_max,
        date_min=date_min,
        network_id=time_series.network.code,
        network_query=network_query,
        network_region_query=network_region_query,
        groups_additional=groups_additional,
    )

    return dedent(query)


def power_network_fueltech_query(
    time_series: TimeSeries,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:
    """Query power stats"""

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
    select
        t.trading_interval,
        t.fueltech_code,
        sum(t.fueltech_power)
    from (
        select
            time_bucket_gapfill('{trunc}', fs.trading_interval) AS trading_interval,
            ft.code as fueltech_code,
            coalesce(avg(fs.generated), 0) as fueltech_power
        from facility_scada fs
        join facility f on fs.facility_code = f.code
        join fueltech ft on f.fueltech_id = ft.code
        where
            fs.is_forecast is False and
            f.fueltech_id is not null and
            f.fueltech_id not in ({fueltechs_exclude}) and
            {network_query}
            {network_region_query}
            fs.trading_interval <= '{date_max}' and
            fs.trading_interval >= '{date_min}'
            {fueltech_filter}
        group by 1, f.code, 2
    ) as t
    group by 1, 2
    order by 1 desc
    """

    network_region_query: str = ""
    fueltech_filter: str = ""
    wem_apvi_case: str = ""
    timezone: str = time_series.network.timezone_database

    fueltechs_excluded = ["exports", "imports", "interconnector"]

    if NetworkNEM in networks_query or NetworkWEM in networks_query:
        fueltechs_excluded.append("solar_rooftop")

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "

    if NetworkWEM in networks_query:
        # silly single case we'll refactor out
        # APVI network is used to provide rooftop for WEM so we require it
        # in country-wide totals
        wem_apvi_case = "or (f.network_id='APVI' and f.network_region='WEM')"

    network_query = "(f.network_id IN ({}) {}) and ".format(
        networks_to_in(networks_query), wem_apvi_case
    )

    date_max = time_series.get_range().end
    date_min = time_series.get_range().start

    fueltechs_exclude = ", ".join("'{}'".format(i) for i in fueltechs_excluded)

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=time_series.interval.interval_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            fueltech_filter=fueltech_filter,
            wem_apvi_case=wem_apvi_case,
            fueltechs_exclude=fueltechs_exclude,
        )
    )

    return query


def power_network_rooftop_query(
    time_series: TimeSeries,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
    forecast: bool = False,
) -> str:
    """Query power stats"""

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
        select
            time_bucket_gapfill('30 minutes', fs.trading_interval)  AS trading_interval,
            ft.code as fueltech_code,
            coalesce({agg_func}(fs.generated), 0) as facility_power
        from facility_scada fs
        join facility f on fs.facility_code = f.code
        join fueltech ft on f.fueltech_id = ft.code
        where
            {forecast_query}
            f.fueltech_id = 'solar_rooftop' and
            {network_query}
            {network_region_query}
            fs.trading_interval <= '{date_max}' and
            fs.trading_interval >= '{date_min}'
        group by 1, 2
        order by 1 desc
    """

    network_region_query: str = ""
    wem_apvi_case: str = ""
    agg_func = "sum"
    timezone: str = time_series.network.timezone_database

    forecast_query = f"fs.is_forecast is {forecast} and"

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "

    if NetworkWEM in networks_query:
        # silly single case we'll refactor out
        # APVI network is used to provide rooftop for WEM so we require it
        # in country-wide totals
        wem_apvi_case = "or (f.network_id='APVI' and f.network_region='WEM')"

        if NetworkAPVI in networks_query:
            networks_query.remove(NetworkAPVI)

        if NetworkNEM not in networks_query:
            agg_func = "max"

    network_query = "(f.network_id IN ({}) {}) and ".format(
        networks_to_in(networks_query), wem_apvi_case
    )

    date_max = time_series.get_range().end
    date_min = time_series.get_range().start

    if forecast:
        # @TODO work out what in get_range is mashing this
        date_min = time_series.start + timedelta(minutes=30)
        date_max = date_min + timedelta(hours=3)

    query = dedent(
        __query.format(
            network_query=network_query,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            forecast_query=forecast_query,
            agg_func=agg_func,
        )
    )

    return query


"""
Energy Queries
"""


def energy_network_fueltech_query(
    time_series: TimeSeries,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
    coalesce_with: Optional[int] = 0,
) -> str:
    """
    Get Energy for a network or network + region
    based on a year
    """

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
    select
        date_trunc('{trunc}', t.trading_day),
        t.fueltech_id,
        coalesce(sum(t.energy) / 1000, {coalesce_with}) as fueltech_energy,
        coalesce(sum(t.market_value), {coalesce_with}) as fueltech_market_value,
        coalesce(sum(t.emissions), {coalesce_with}) as fueltech_emissions
    from at_facility_daily t
    left join facility f on t.facility_code = f.code
    where
        t.trading_day <= '{date_max}'::date and
        t.trading_day >= '{date_min}'::date and
        t.fueltech_id not in ('imports', 'exports', 'interconnector') and
        {network_query}
        {network_region_query}
        1=1
    group by 1, 2
    order by 1 desc;
    """

    network_region_query = ""
    date_range = time_series.get_range()

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and"

    networks_list = networks_to_in(networks_query)
    network_query = "t.network_id IN ({}) and ".format(networks_list)

    query = dedent(
        __query.format(
            trunc=date_range.interval.trunc,
            date_min=date_range.start.date(),
            date_max=date_range.end.date(),
            network_query=network_query,
            network_region_query=network_region_query,
            coalesce_with=coalesce_with,
        )
    )

    return query


def energy_network_flow_query(
    time_series: TimeSeries,
    network_region: str,
    networks_query: Optional[List[NetworkSchema]] = None,
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

    query = dedent(
        __query.format(
            network_region=network_region,
            trunc=date_range.interval.trunc,
            date_min=date_range.start,
            date_max=date_range.end,
        )
    )

    return query


def energy_network_interconnector_emissions_query(
    time_series: TimeSeries,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
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
        t.network_id,
        t.network_region,
        coalesce(t.energy_imports / 10000, 0),
        coalesce(t.energy_exports / 10000, 0),
        t.emissions_imports,
        t.emissions_exports
    from at_network_flows t
    where
        t.trading_interval <= '{date_max}' and
        t.trading_interval >= '{date_min}' and
        t.network_id = '{network_id}' and
        {network_region_query}
    order by 1 desc

    """

    timezone = time_series.network.timezone_database
    network_region_query = ""
    date_range = time_series.get_range()

    if network_region:
        network_region_query = f"""
            t.network_region = '{network_region}'
        """

    query = dedent(
        __query.format(
            timezone=timezone,
            # trunc=date_range.interval.trunc,
            network_id=time_series.network.code,
            date_min=date_range.start,
            date_max=date_range.end,
            network_region_query=network_region_query,
        )
    )

    return query
