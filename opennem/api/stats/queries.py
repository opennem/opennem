"""
    Queries for network data

    @TODO make these pluggable
    @TODO use sqlalchemy text() compiled queries
"""

from datetime import datetime
from typing import List, Optional

from opennem.core.networks import network_from_network_region
from opennem.core.normalizers import normalize_duid
from opennem.db.models.opennem import Network
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod


def duid_in_case(facility_codes: List[str]) -> str:
    return ",".join(
        ["'{}'".format(i) for i in map(normalize_duid, facility_codes)]
    )


def power_facility(
    facility_codes: List[str],
    network_code: str,
    interval: TimeInterval,
    period: TimePeriod,
) -> str:

    timezone = "UTC"

    network = network_from_network_region(network_code)
    timezone = network.get_timezone(postgres_format=True)

    __query = """
        SET SESSION TIME ZONE '{timezone}';

        select
            t.trading_interval,
            coalesce(avg(t.facility_power), 0),
            t.facility_code
        from (
            select
                time_bucket_gapfill('{trunc}', trading_interval) AS trading_interval,
                interpolate(
                    max(fs.generated)
                ) as facility_power,
                fs.facility_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            where
                fs.trading_interval <= now()
                and fs.trading_interval >= now() - '{period}'::interval
                and fs.facility_code in ({facility_codes_parsed})
            group by 1, 3
        ) as t
        group by 1, 3
        order by 1 desc
    """

    query = __query.format(
        facility_codes_parsed=duid_in_case(facility_codes),
        network_code=network_code,
        trunc=interval.interval_sql,
        period=period.period_sql,
        timezone=timezone,
    )

    return query


def power_network(
    network_code: str, interval: TimeInterval, period: TimePeriod,
) -> str:

    scale = 1

    network = network_from_network_region(network_code)
    timezone = network.timezone_database

    if not timezone:
        timezone = "UTC"

    __query = """
        with intervals as (
            select generate_series(
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}') - '{period}'::interval,
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}'),
                '{interval}'::interval
            )::timestamp as interval
        )

        select
            i.interval as trading_day,
            fs.generated,
            fs.facility_code as facility_code
        from intervals i
        left outer join
            (select
                date_trunc('{trunc}', fs.trading_interval AT TIME ZONE '{timezone}')::timestamp  {interval_remainder} as interval,
                fs.facility_code,
                coalesce(avg(generated), 0) as generated
                from facility_scada fs
                where
                    fs.trading_interval > now() AT TIME ZONE '{timezone}' - '{period}'::interval
                    and fs.network_id = '{network_code}'
                group by 1, 2
            ) as fs on fs.interval = i.interval
        order by 1 desc, 2 desc
    """

    query = __query.format(
        network_code=network_code,
        trunc=interval.trunc,
        interval=interval.interval_human,
        interval_remainder=interval.get_sql_join(
            timezone=network.timezone_database
        ),
        period=period.period_sql,
        scale=scale,
        timezone=timezone,
    )

    return query


def power_network_fueltech(
    network: NetworkSchema,
    interval: TimeInterval,
    period: TimePeriod,
    network_region: str = None,
) -> str:

    timezone = network.get_timezone(postgres_format=True)

    if not timezone:
        timezone = "UTC"

    __query = """
        SET SESSION TIME ZONE '{timezone}';

        select
            t.trading_interval,
            sum(t.facility_power),
            t.fueltech_code
        from (
            select
                time_bucket_gapfill('{trunc}', trading_interval) AS trading_interval,
                interpolate(
                    max(fs.generated)
                ) as facility_power,
                fs.facility_code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.trading_interval <= now()
                and fs.trading_interval >= now() - '{period}'::interval
                and fs.network_id = '{network_code}'
                and f.fueltech_id is not null
                {network_region_query}
            group by 1, 3, 4
        ) as t
        group by 1, 3
        order by 1 desc
    """

    network_region_query = ""

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    query = __query.format(
        network_code=network.code,
        trunc=interval.interval_sql,
        period=period.period_sql,
        network_region_query=network_region_query,
        timezone=timezone,
    )

    return query


def energy_facility(
    facility_codes: List[str],
    network_code: str,
    interval: TimeInterval,
    period: TimePeriod,
) -> str:

    network = network_from_network_region(network_code)
    timezone = network.timezone_database

    __query = """
        with intervals as (
            select generate_series(
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}') - '{period}'::interval,
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}'),
                '{interval}'::interval
            )::timestamp as interval
        )

        select
            i.interval as trading_day,
            fs.generated,
            fs.facility_code as facility_code
        from intervals i
        left outer join
            (select
                date_trunc('{trunc}', fs.trading_interval AT TIME ZONE '{timezone}')::timestamp  {interval_remainder} as interval,
                fs.facility_code,
                coalesce(sum(fs.eoi_quantity), NULL) / {scale} as generated
                from facility_scada fs
                where
                    fs.facility_code in ({facility_codes_parsed})
                    and fs.trading_interval > now() AT TIME ZONE '{timezone}' - '{period}'::interval
                    and fs.network_id = '{network_code}'
                group by 1, 2
            ) as fs on fs.interval = i.interval
        order by 1 desc, 2 asc"""

    query = __query.format(
        facility_codes_parsed=duid_in_case(facility_codes),
        network_code=network_code,
        trunc=interval.trunc,
        interval=interval.interval_sql,
        interval_remainder=interval.get_sql_join(
            timezone=network.timezone_database
        ),
        period=period.period_sql,
        scale=network.intervals_per_hour,
        timezone=timezone,
    )

    return query


def energy_network(
    network: NetworkSchema, interval: TimeInterval, period: TimePeriod,
) -> str:

    timezone = network.timezone_database

    __query = """
        with intervals as (
            select generate_series(
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}') - '{period}'::interval,
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}'),
                '{interval}'::interval
            )::timestamp as interval
        )

        select
            i.interval as trading_day,
            fs.generated,
            fs.facility_code as facility_code
        from intervals i
        left outer join
            (select
                date_trunc('{trunc}', fs.trading_interval AT TIME ZONE '{timezone}')::timestamp  {interval_remainder} as interval,
                fs.facility_code,
                coalesce(sum(fs.eoi_quantity), NULL) / {scale} as generated
                from facility_scada fs
                where
                    fs.trading_interval > now() AT TIME ZONE '{timezone}' - '{period}'::interval
                    and fs.network_id = '{network_code}'
                group by 1, 2
            ) as fs on fs.interval = i.interval
        order by 1 desc, 2 asc"""

    query = __query.format(
        network_code=network.code,
        trunc=interval.trunc,
        interval=interval.interval_sql,
        interval_remainder=interval.get_sql_join(
            timezone=network.timezone_database
        ),
        period=period.period_sql,
        scale=network.intervals_per_hour,
        timezone=timezone,
    )

    return query


def energy_network_fueltech(
    network: NetworkSchema,
    interval: TimeInterval,
    period: TimePeriod,
    network_region: str = None,
) -> str:

    timezone = network.timezone_database

    if not timezone:
        timezone = "UTC"

    __query = """
        with intervals as (
            select generate_series(
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}') - '{period}'::interval,
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}'),
                '{interval}'::interval
            )::timestamp as interval
        )

        select
            i.interval as trading_day,
            fs.generated,
            fs.code
        from intervals i
        left outer join
            (
                select
                    date_trunc('{trunc}', fs.trading_interval AT TIME ZONE '{timezone}')::timestamp  {interval_remainder} as interval,
                    ft.code,
                    coalesce(sum(fs.eoi_quantity), 0) / {scale} as generated
                from facility_scada fs
                join facility f on fs.facility_code = f.code
                join fueltech ft on f.fueltech_id = ft.code
                where
                    fs.trading_interval > now() AT TIME ZONE '{timezone}' - '{period}'::interval
                    and fs.network_id = '{network_code}'
                    and f.fueltech_id is not null
                    {network_region_query}
                group by 1, 2
            ) as fs on fs.interval = i.interval
        order by 1 desc, 2 desc"""

    network_region_query = ""

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    query = __query.format(
        network_code=network.code,
        trunc=interval.trunc,
        interval=interval.interval_sql,
        interval_remainder=interval.get_sql_join(
            timezone=network.timezone_database
        ),
        period=period.period_sql,
        scale=network.intervals_per_hour,
        network_region_query=network_region_query,
        timezone=timezone,
    )

    return query


def energy_network_fueltech_year(
    network: NetworkSchema,
    interval: TimeInterval,
    year: int,
    network_region: str = None,
) -> str:
    """
        Get Energy for a network or network + region
        based on a year
    """

    timezone = network.get_timezone(postgres_format=True)

    if not timezone:
        timezone = "UTC"

    year_max = "{}-12-31".format(year)

    if year == datetime.now().year:
        year_max = "now()"

    __query = """
        SET SESSION TIME ZONE '{timezone}';

        select
            t.trading_interval,
            sum(t.facility_energy),
            t.fueltech_code
        from (
            select
                time_bucket_gapfill('{trunc}', trading_interval) AS trading_interval,
                on_energy_sum(fs.generated, '{trunc}') as facility_energy,
                f.code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.trading_interval >= '{year}-01-01'
                and fs.trading_interval <= '{year_max}'
                and fs.network_id = '{network_code}'
                and f.fueltech_id is not null
                {network_region_query}
            group by 1, 3, 4
        ) as t
        group by 1, 3
        order by 1 desc;
    """

    network_region_query = ""

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    query = __query.format(
        network_code=network.code,
        trunc=interval.interval_sql,
        year=year,
        year_max=year_max,
        scale=network.intervals_per_hour,
        network_region_query=network_region_query,
        timezone=timezone,
    )

    return query


def energy_network_fueltech_all(
    network: Optional[NetworkSchema], network_region: Optional[str],
):
    timezone = "AEST"

    if network:
        timezone = network.timezone_database

    __query = """
    with intervals as (
        select generate_series(
            date_trunc('month', (select min(trading_interval) from facility_scada)),
            date_trunc('month', now() AT TIME ZONE 'AEST'),
            '1 Month'::interval
        )::timestamp as interval
    )

    select
        i.interval as trading_day,
        fs.energy,
        fs.code
    from intervals i
    left outer join
        (
            select
                date_trunc('month', fs.trading_interval AT TIME ZONE 'AEST')::timestamp as interval,
                ft.code,
                coalesce(on_energy_sum(fs.generated, '1 Month'), 0) as energy
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.trading_interval >= (select min(trading_interval) from facility_scada)
                and f.fueltech_id is not null
                {network_query}
                {network_region_query}
            group by 1, 2
        ) as fs on fs.interval = i.interval
    order by 1 desc, 2 desc;
    """

    network_query = ""
    network_region_query = ""

    if network:
        network_query = f"and fs.network_id = '{network.code}' "

    if network_region:
        network_region_query = f"and f.network_region='{network_region}' "

    query = __query.format(
        network_query=network_query,
        network_region_query=network_region_query,
        timezone=timezone,
    )

    return query


def price_network_region(
    network: NetworkSchema,
    region_code: str,
    interval: TimeInterval,
    period: TimePeriod,
) -> str:

    timezone = network.timezone_database

    if not timezone:
        timezone = "UTC"

    __query = """with intervals as (
            select generate_series(
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}') - '{period}'::interval,
                date_trunc('{trunc}', now() AT TIME ZONE '{timezone}'),
                '{interval}'::interval
            )::timestamp as interval
        )

        select
            i.interval as trading_day,
            fs.generated,
            fs.network_region
        from intervals i
        left outer join
            (select
                date_trunc('{trunc}', fs.trading_interval AT TIME ZONE '{timezone}')::timestamp  {interval_remainder} as interval,
                fs.network_region,
                coalesce(avg(fs.price), NULL) as generated
                from balancing_summary fs
                where
                    fs.trading_interval > now() AT TIME ZONE '{timezone}' - '{period}'::interval
                    and fs.network_id = '{network_code}'
                    and fs.network_region = '{network_region}'
                group by 1, 2
            ) as fs on fs.interval = i.interval
        order by 1 desc, 2 asc"""

    query = __query.format(
        network_code=network.code,
        network_region=region_code,
        trunc=interval.trunc,
        interval=interval.interval_sql,
        interval_remainder=interval.get_sql_join(
            timezone=network.timezone_database
        ),
        period=period.period_sql,
        scale=network.intervals_per_hour,
        timezone=timezone,
    )

    return query
