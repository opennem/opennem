from textwrap import dedent
from typing import List, Optional

from sqlalchemy import sql
from sqlalchemy.sql.elements import TextClause

from opennem.api.stats.controllers import networks_to_in
from opennem.schema.dates import TimeSeries
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.schema.stats import StatTypes
from opennem.settings import settings


def weather_observation_query(time_series: TimeSeries, station_codes: List[str]) -> str:

    if time_series.interval.interval > 1440:
        # @TODO replace with mv
        __query = """
        select
            date_trunc('{trunc}', t.observation_time at time zone '{tz}') as observation_month,
            t.station_id,
            avg(t.temp_avg),
            min(t.temp_min),
            max(t.temp_max)
        from
            (
                select
                    time_bucket_gapfill('1 day', observation_time) as observation_time,
                    fs.station_id,
                    avg(fs.temp_air) as temp_avg,

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
        group by 1, 2;
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
            time_bucket_gapfill('{interval_sql}', observation_time) as ot,
            fs.station_id as station_id,
            avg(fs.temp_air) as temp_air,

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
        group by 1, 2;
        """.format(
            interval_sql=time_series.interval.interval_sql,
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
    order by trading_interval asc;


    """.format(
        timezone=time_series.network.timezone_database,
        network_id=time_series.network.code,
        region=network_region,
        date_start=time_series.get_range().start,
        date_end=time_series.get_range().end,
    )

    return dedent(___query)


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
            bs.trading_interval > '{date_min}' and
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
    order by 1 asc;
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
        time_bucket_gapfill('{trunc}', fs.trading_interval) AS trading_interval,
        ft.code as fueltech_code,
        sum(fs.generated) as facility_power
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
        fs.trading_interval > '{date_min}'
        {fueltech_filter}
    group by 1, 2
    """

    network_region_query: str = ""
    fueltech_filter: str = ""
    wem_apvi_case: str = ""
    timezone: str = time_series.network.timezone_database

    fueltechs_excluded = ["exports", "imports"]

    if NetworkNEM in networks_query:
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
            fs.is_forecast is {forecast} and
            f.fueltech_id = 'solar_rooftop' and
            {network_query}
            {network_region_query}
            fs.trading_interval <= '{date_max}' and
            fs.trading_interval > '{date_min}'
        group by 1, 2
        order by 1 asc
    """

    network_region_query: str = ""
    wem_apvi_case: str = ""
    agg_func = "sum"
    timezone: str = time_series.network.timezone_database

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "

    if NetworkWEM in networks_query:
        # silly single case we'll refactor out
        # APVI network is used to provide rooftop for WEM so we require it
        # in country-wide totals
        wem_apvi_case = "or (f.network_id='APVI' and f.network_region='WEM')"
        agg_func = "max"

    network_query = "(f.network_id IN ({}) {}) and ".format(
        networks_to_in(networks_query), wem_apvi_case
    )

    date_max = time_series.get_range().end
    date_min = time_series.get_range().start

    query = dedent(
        __query.format(
            network_query=network_query,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            forecast=str(forecast),
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
) -> str:
    """
    Get Energy for a network or network + region
    based on a year
    """

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    if time_series.interval.interval > 1440:
        __query = """
        select
            date_trunc('{trunc}', t.trading_day) as trading_month,
            t.fueltech_id,
            coalesce(sum(t.fueltech_energy) / 1000 , 0) as fueltech_energy,
            sum(t.fueltech_market_value) as fueltech_market_value,
            coalesce(sum(t.fueltech_emissions), 0) as fueltech_emissions
        from
            (select
                time_bucket_gapfill('1 day', t.ti_day_aest) as trading_day,
                t.fueltech_id,
                sum(t.energy) as fueltech_energy,
                sum(t.market_value) as fueltech_market_value,
                sum(t.emissions) as fueltech_emissions
            from {energy_view} t
            where
                t.ti_day_aest <= '{date_max}' and
                t.ti_day_aest >= '{date_min}' and
                t.fueltech_id not in ('imports', 'exports') and
                {network_query}
                {network_region_query}
                1=1
            group by 1, 2) as t
        group by 1, 2
        order by
            1 desc;
        """
    else:
        __query = """
        select
            t.ti_{trunc_name} as trading_day,
            t.fueltech_id,
            coalesce(sum(t.energy) / 1000, 0) as fueltech_energy,
            sum(t.market_value) as fueltech_market_value,
            coalesce(sum(t.emissions), 0) as fueltech_emissions
        from {energy_view} t
        where
            t.trading_interval <= '{date_max}' and
            t.trading_interval >= '{date_min}' and
            t.fueltech_id not in ('imports', 'exports') and
            {network_query}
            {network_region_query}
            1=1
        group by 1, 2
        order by
            trading_day desc;
        """

    network_region_query = ""
    date_range = time_series.get_range()

    if network_region:
        network_region_query = f"t.network_region='{network_region}' and"

    networks_list = networks_to_in(networks_query)
    network_query = "t.network_id IN ({}) and ".format(networks_list)

    trunc_name = "{}_{}".format(
        time_series.interval.trunc, time_series.network.timezone_database
    ).lower()

    query = dedent(
        __query.format(
            energy_view=settings.db_energy_view,
            trunc=date_range.interval.trunc,
            trunc_name=trunc_name,
            date_min=date_range.start,
            date_max=date_range.end,
            network_query=network_query,
            network_region_query=network_region_query,
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
        sum(t.exports_energy)
    from (
        select
            ei.trading_interval,
            ei.imports_energy,
            ei.exports_energy
        from mv_interchange_energy_nem_region ei
        where
            ei.trading_interval <= '{date_max}'
            and ei.trading_interval >= '{date_min}'
            and ei.network_region='{network_region}'
    ) as t
    group by 1
    order by 1 asc
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
    date_range = time_series.get_range()

    if network_region:
        network_region_query = f"""
            (t.flow_from='{network_region}' or t.flow_to='{network_region}') and
        """

    query = dedent(
        __query.format(
            timezone=timezone,
            # trunc=date_range.interval.trunc,
            date_min=date_range.start,
            date_max=date_range.end,
            network_region_query=network_region_query,
        )
    )

    return query
