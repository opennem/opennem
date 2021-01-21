from datetime import datetime, timedelta
from textwrap import dedent
from typing import List, Optional

from sqlalchemy import sql
from sqlalchemy.sql.elements import TextClause

from opennem.api.stats.controllers import get_scada_range, networks_to_in
from opennem.api.stats.schema import ScadaDateRange
from opennem.schema.network import NetworkSchema, NetworkWEM
from opennem.schema.stats import StatTypes
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.dates import subtract_week


def interconnector_flow_power_query(
    network_region: str, date_range: ScadaDateRange, network: NetworkSchema
) -> str:
    __query = """
            select
                -- time_bucket_gapfill('5 minutes', trading_interval) as trading_interval,
                trading_interval at time zone '{timezone}' as trading_interval,
                max(fs.facility_power) as facility_power,
                f.network_region as flow_from,
                f.interconnector_region_to as flow_to
            from mv_nem_facility_power_5min fs
            join facility f on fs.facility_code = f.code
            where
                f.interconnector is True and
                (f.network_region= '{region}' or f.interconnector_region_to= '{region}') and
                fs.trading_interval <= '{date_end}' and
                fs.trading_interval > '{date_start}'
            group by 1, f.code, 3, 4
            order by trading_interval desc;
           """.format(
        timezone=network.timezone_database,
        region=network_region,
        date_start=subtract_week(date_range.get_end()),
        date_end=date_range.get_end(),
    )

    return dedent(__query)


def interconnector_power_flow(
    network_region: str, date_range: ScadaDateRange, network: NetworkSchema
) -> str:
    """Get region flows using materialized view"""
    ___query = """
        select
            trading_interval at time zone '{timezone}' as trading_interval,
            fs.network_region,
            fs.imports,
            fs.exports
        from mv_interchange_power_nem_region fs
        where
            fs.network_id = '{network_id}' and
            fs.network_region= '{region}' and
            fs.trading_interval <= '{date_end}' and
            fs.trading_interval > '{date_start}'
        order by trading_interval desc;
    """.format(
        timezone=network.timezone_database,
        network_id=network.code,
        region=network_region,
        date_start=subtract_week(date_range.get_end()),
        date_end=date_range.get_end(),
    )

    return dedent(___query)


def interconnector_net_energy_flow(network_region: str, date_range: ScadaDateRange) -> TextClause:
    """Get interconnector energy flows for a region"""
    __query = sql.text(
        dedent(
            """
            select
                f.trading_interval,
                max(f.energy) as facility_energy,
                f.network_region as flow_from,
                f.interconnector_region_to as flow_to
            from mv_facility_all f
            where
                f.interconnector is True and
                (f.network_region= :region or f.interconnector_region_to= :region) and
                f.trading_interval <= :date_end and
                f.trading_interval > :date_start
            group by 1, 3, 4
           """
        )
    ).bindparams(
        region=network_region,
        date_start=date_range.get_start(),
        date_end=date_range.get_end(),
    )

    return __query


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
    interval: TimeInterval,
    network: NetworkSchema = NetworkWEM,
    group_field: str = "bs.network_id",
    date_range: Optional[ScadaDateRange] = None,
    period: Optional[TimePeriod] = None,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:

    if not networks_query:
        networks_query = [network]

    if network not in networks_query:
        networks_query.append(network)

    if not date_range:
        date_range = get_scada_range(network=network, networks=networks_query)

    # timezone = network.get_timezone(postgres_format=True)
    timezone = network.timezone_database

    __query = """
        select
            trading_interval at time zone '{timezone}',
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

    network_region_query = ""

    if network_region:
        network_region_query = f"bs.network_region='{network_region}' and "
        group_field = "bs.network_region"

    network_query = "bs.network_id IN ({}) and ".format(networks_to_in(networks_query))

    if len(networks_query) > 1:
        group_field = "'AU'"

    if not date_range:
        raise Exception("Require a date range")

    date_max = date_range.get_end()
    date_min = date_range.get_start()

    if period:
        date_min = date_range.get_end() - timedelta(minutes=period.period)

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=interval.interval_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            group_field=group_field,
        )
    )

    return query


def power_network_fueltech_query(
    interval: TimeInterval,
    network: NetworkSchema = NetworkWEM,
    date_range: Optional[ScadaDateRange] = None,
    period: Optional[TimePeriod] = None,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:
    """Query power stats"""

    if not networks_query:
        networks_query = [network]

    if network not in networks_query:
        networks_query.append(network)

    if not date_range:
        date_range = get_scada_range(network=network, networks=networks_query)

    __query = """
        select
            fs.trading_interval at time zone '{timezone}' AS trading_interval,
            ft.code as fueltech_code,
            sum(fs.facility_power) as facility_power
        from mv_nem_facility_power_5min fs
        join facility f on fs.facility_code = f.code
        join fueltech ft on f.fueltech_id = ft.code
        where
            f.fueltech_id is not null and
            f.fueltech_id not in ('exports', 'imports') and
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
    timezone: str = network.timezone_database

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "
    else:
        fueltech_filter = "and f.fueltech_id not in ('imports', 'exports') "

    if NetworkWEM in networks_query:
        # silly single case we'll refactor out
        # APVI network is used to provide rooftop for WEM so we require it
        # in country-wide totals
        wem_apvi_case = "or (f.network_id='APVI' and f.network_region='WEM')"

    network_query = "(f.network_id IN ({}) {}) and ".format(
        networks_to_in(networks_query), wem_apvi_case
    )

    if not date_range:
        raise Exception("Require a date range")

    date_max = date_range.get_end()
    date_min = date_range.get_start()

    if period:
        date_min = date_range.get_end() - timedelta(minutes=period.period)

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=interval.interval_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            fueltech_filter=fueltech_filter,
            wem_apvi_case=wem_apvi_case,
        )
    )

    return query


def energy_network_fueltech_query(
    network: NetworkSchema,
    interconnector: bool = False,
    interval: Optional[TimeInterval] = None,
    year: Optional[int] = None,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
    date_range: Optional[ScadaDateRange] = None,
) -> str:
    """
    Get Energy for a network or network + region
    based on a year
    """

    if not networks_query:
        networks_query = [network]

    if network not in networks_query:
        networks_query.append(network)

    __query = """
    select
        t.ti_{trunc_name} as trading_day,
        t.fueltech_id,
        sum(t.energy) / 1000 as fueltech_energy,
        sum(t.market_value) as fueltech_market_value,
        sum(t.emissions) as fueltech_emissions
    from mv_facility_all t
    where
        t.trading_interval <= '{year_max}' and
        t.trading_interval >= '{year_min}' and
        {network_query}
        {network_region_query}
        {fueltech_filter}
        1=1
    group by 1, 2
    order by
        trading_day desc;
    """

    if interconnector:
        # __query = """
        # select
        #     t.ti_{trunc_name} as trading_day,
        #     sum(t.energy) / 1000 as interconnector_energy,
        #     t.network_region as flow_from,
        #     t.interconnector_region_to as flow_to,
        #     t.network_region || '->' || t.interconnector_region_to as flow_region
        # from mv_facility_all t
        # where
        #     t.interconnector is True and
        #     t.trading_interval <= '{year_max}' and
        #     t.trading_interval >= '{year_min}' and
        #     {network_query}
        #     {network_region_query}
        #     {fueltech_filter}
        #     1=1
        # group by 1, 5, 3, 4
        # order by
        #     trading_day desc;
        # """

        __query = """
        select
            date_trunc('{trunc}', t.trading_interval) as trading_day,
            max(t.imports_avg) / 1000,
            max(t.exports_avg) / 1000
        from mv_interchange_energy_nem_region t
        where
            t.trading_interval <= '{year_max}' and
            t.trading_interval >= '{year_min}' and
            {network_query}
            {network_region_query}
            1=1
        group by 1
        order by 1 desc

        """

    timezone = network.timezone_database
    offset = network.get_timezone(postgres_format=True)

    if not date_range:
        date_range = get_scada_range(network=network, networks=networks_query)

    if not date_range:
        raise Exception("Require a scada range for {}".format(network.code))

    network_region_query = ""
    fueltech_filter = ""

    if network_region:
        network_region_interconnector = ""

        if interconnector:
            network_region_interconnector = f" or t.interconnector_region_to='{network_region}'"

        network_region_query = f"t.network_region='{network_region}' and"

    fueltech_filter = "t.fueltech_id not in ('imports', 'exports') and "

    # if interconnector:
    # fueltech_filter = "t.fueltech_id in ('imports', 'exports') and "

    networks_list = networks_to_in(networks_query)
    network_query = "t.network_id IN ({}) and ".format(networks_list)

    if not timezone:
        timezone = "UTC"

    trunc = None

    if interval:
        trunc = interval.trunc

    if year:
        # might have to do +offset times
        year_max = "{}-12-31 23:59:59{}".format(year, offset)
        year_min = "{}-01-01 00:00:00{}".format(year, offset)

        if year == datetime.now().year:
            year_max = date_range.get_end()

        if not trunc:
            trunc = "day"
    else:
        year_min = date_range.get_start()
        year_max = date_range.get_end()

        if not trunc:
            trunc = "month"

    trunc_name = "{}_{}".format(trunc, timezone).lower()

    query = dedent(
        __query.format(
            trunc=trunc,
            trunc_name=trunc_name,
            year_min=year_min,
            year_max=year_max,
            network_query=network_query,
            network_region_query=network_region_query,
            fueltech_filter=fueltech_filter,
        )
    )

    return query
