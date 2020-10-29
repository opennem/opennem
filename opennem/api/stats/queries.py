"""
    Queries for network data

    @TODO make these pluggable
    @TODO use sqlalchemy text() compiled queries
"""

from datetime import datetime
from typing import List, Optional

from fastapi.exceptions import HTTPException
from starlette import status

from opennem.api.stats.schema import ScadaDateRange
from opennem.core.networks import network_from_network_region
from opennem.core.normalizers import normalize_duid
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
                coalesce(
                    avg(fs.generated), 0
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
    network_region: Optional[str] = None,
    scada_range: Optional[ScadaDateRange] = None,
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
                coalesce(
                    avg(fs.generated), 0
                ) as facility_power,
                fs.facility_code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.trading_interval <= {date_end}
                and fs.trading_interval >= {date_end}::timestamp - '{period}'::interval
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

    date_end = "now()"

    if scada_range:
        date_end = scada_range.get_end_sql()

    query = __query.format(
        network_code=network.code,
        trunc=interval.interval_sql,
        period=period.period_sql,
        network_region_query=network_region_query,
        timezone=timezone,
        date_end=date_end,
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
    scada_range: ScadaDateRange = None,
) -> str:
    """
        Get Energy for a network or network + region
        based on a year
    """

    timezone = network.get_timezone(postgres_format=True)

    if not timezone:
        timezone = "UTC"

    year_max = "'{}-12-31'".format(year)

    if year == datetime.now().year:
        year_max = scada_range.get_end_sql(as_date=False)

    __query = """
        SET SESSION TIME ZONE '{timezone}';

        select
            t.trading_interval,
            sum(t.facility_energy),
            t.fueltech_code
        from (
            select
                time_bucket_gapfill('{trunc}', trading_interval) AS trading_interval,
                energy_sum(fs.generated, '{trunc}') * interval_size('1 day', count(fs.generated)) / 1000 as facility_energy,
                f.code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.trading_interval >= '{year}-01-01'
                and fs.trading_interval <= {year_max}
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
    network: Optional[NetworkSchema],
    network_region: Optional[str],
    scada_range: ScadaDateRange,
):
    timezone = "AEST"

    if network:
        timezone = network.get_timezone(postgres_format=True)

    __query = """

        SET SESSION TIME ZONE '{timezone}';

        select
            date_trunc('month', t.trading_interval),
            sum(t.facility_energy),
            t.fueltech_code
        from (
            select
                time_bucket_gapfill('1 day', trading_interval) AS trading_interval,
                energy_sum(fs.generated, '1 day') * interval_size('1 day', count(fs.generated)) / 1000 as facility_energy,
                f.code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.trading_interval >= {scada_min}
                and fs.trading_interval <= {scada_max}
                and f.fueltech_id is not null
                {network_query}
                {network_region_query}
            group by 1, 3, 4
        ) as t
        group by 1, 3
        order by 1 desc;
    """

    network_query = ""
    network_region_query = ""

    if network:
        network_query = f"and fs.network_id = '{network.code}' "

    if network_region:
        network_region_query = f"and f.network_region='{network_region}' "

    query = __query.format(
        network_code=network.code,
        network_query=network_query,
        network_region_query=network_region_query,
        scada_min=scada_range.get_start_sql(as_date=True),
        scada_max=scada_range.get_end_sql(as_date=True),
        timezone=timezone,
    )

    return query


def price_network_region(
    network: NetworkSchema,
    network_region_code: str,
    interval: TimeInterval,
    period: TimePeriod,
    scada_range: ScadaDateRange,
    year: Optional[int] = None,
) -> str:

    timezone = network.get_timezone(postgres_format=True)

    if not timezone:
        timezone = "UTC"

    __query = """
        SET SESSION TIME ZONE '{timezone}';

        select
            time_bucket_gapfill('{trunc}', bs.trading_interval) AS trading_interval,
            bs.network_region,
            coalesce(avg(bs.price), 0) as price
        from balancing_summary bs
        where
            bs.trading_interval >= {date_min_query}
            and bs.trading_interval <= {scada_max}
            {network_query}
            {network_region_query}
        group by 1, 2
        order by 1 desc
    """

    network_query = ""
    network_region_query = ""

    if network:
        network_query = f"and bs.network_id = '{network.code}' "

    if network_region_code:
        network_region_query = (
            f"and bs.network_region='{network_region_code}' "
        )

    date_min_query = ""

    if period:
        date_min_query = "{scada_max}::timestamp - interval '{period}'::interval".format(
            scada_max=scada_range.get_end_sql(), period=period.period_sql
        )

    if year:
        date_min_query = "'{year}-01-01'::date ".format(year=year)

    if not period and not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Require one of period or year",
        )

    query = __query.format(
        trunc=interval.interval_sql,
        timezone=timezone,
        network_query=network_query,
        network_region_query=network_region_query,
        scada_max=scada_range.get_end_sql(),
        date_min_query=date_min_query,
    )

    return query


def price_network_monthly(
    network: Optional[NetworkSchema],
    network_region_code: Optional[str],
    scada_range: ScadaDateRange,
):
    timezone = "AEST"

    networks = [network.code]

    if network.code == "au":
        networks = ["WEM", "NEM"]

    if network:
        timezone = network.get_timezone(postgres_format=True)

    __query = """

        SET SESSION TIME ZONE '{timezone}';

        select
            date_trunc('month', t.trading_interval),
            avg(t.price),
            t.network_id
        from (
            select
                time_bucket_gapfill('1 day', trading_interval) AS trading_interval,
                avg(bs.price) as price,
                bs.network_id as network_id
            from balancing_summary bs
            where
                bs.trading_interval >= {scada_min}
                and bs.trading_interval <= {scada_max}
                and bs.network_id IN ({network_codes})
            group by 1, 3
        ) as t
        group by 1, 3
        order by 1 desc;
    """

    network_codes = ""

    for network_code in networks:
        network_codes = ", ".join("'{}'".format(network_code.upper()))

    query = __query.format(
        network_codes=network_codes,
        scada_min=scada_range.get_start_sql(as_date=True),
        scada_max=scada_range.get_end_sql(as_date=True),
        timezone=timezone,
    )

    return query
