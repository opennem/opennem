"""Runs queries to populate the aggregate tables with facility data"""

import logging
from datetime import date, datetime, timedelta
from textwrap import dedent
from typing import Any

from sqlalchemy import text as sql

from opennem import settings
from opennem.aggregates.utils import get_aggregate_month_range, get_aggregate_year_range
from opennem.db import get_database_engine
from opennem.schema.network import (
    NetworkAEMORooftop,
    NetworkAPVI,
    NetworkNEM,
    NetworkOpenNEMRooftopBackfill,
    NetworkSchema,
    NetworkWEM,
)
from opennem.utils.dates import chop_datetime_microseconds, get_last_completed_interval_for_network, get_today_opennem

logger = logging.getLogger("opennem.aggregates.facility_daily")


class AggregateFacilityDailyException(Exception):
    """ """

    pass


def aggregates_facility_daily_query(date_max: datetime, date_min: datetime, network: NetworkSchema) -> str:
    """This is the query to update the at_facility_daily aggregate"""

    __query = """
    insert into at_facility_daily
        (trading_day, network_id, network_region, facility_code, fueltech_id, energy, market_value, emissions)
        select
            date_trunc('day', fs.trading_interval at time zone n.timezone_database) as trading_day,
            f.network_id,
            f.network_region,
            f.code as facility_code,
            f.fueltech_id,
            sum(fs.energy) as energy,
            sum(fs.market_value) as market_value,
            sum(fs.emissions) as emissions
        from (
            select
                time_bucket_gapfill('{network_interval_size}', fs.trading_interval) as trading_interval,
                fs.facility_code as code,
                f.network_region,
                case
                    when sum(fs.eoi_quantity) > 0 then
                        coalesce(sum(fs.eoi_quantity), 0)
                    else 0
                end as energy,
                case
                    when sum(fs.eoi_quantity) > 0 then
                        sum(fs.eoi_quantity) * coalesce(avg(bs.price), avg(bs.price_dispatch), 0)
                    else 0
                end as market_value,
                case
                    when sum(fs.eoi_quantity) > 0 then
                        coalesce(sum(fs.eoi_quantity), 0) * coalesce(max(f.emissions_factor_co2), 0)
                    else 0
                end as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            left join balancing_summary bs on
                bs.trading_interval {trading_offset} = fs.trading_interval
                and bs.network_id = n.network_price
                and bs.network_region = f.network_region
                and f.network_id = '{network_id}'
            where
                fs.is_forecast is False
                and fs.network_id = '{network_id}'
                and fs.trading_interval >= '{date_min}'
                and fs.trading_interval < '{date_max}'
            group by
                1, 2, 3
        ) as fs
        left join facility f on fs.code = f.code
        left join network n on f.network_id = n.code
        where
            f.fueltech_id is not null
        group by
            1,
            f.network_id,
            f.code,
            f.fueltech_id,
            f.network_region
    on conflict (trading_day, network_id, facility_code) DO UPDATE set
        energy = EXCLUDED.energy,
        market_value = EXCLUDED.market_value,
        emissions = EXCLUDED.emissions;
    """

    trading_offset = "- INTERVAL '5 minutes'" if network in [] else ""

    if date_max <= date_min:
        raise AggregateFacilityDailyException(
            f"aggregates_facility_daily_query: date_max ({date_max}) is before date_min ({date_min})"
        )

    query = __query.format(
        date_min=chop_datetime_microseconds(date_min),
        date_max=chop_datetime_microseconds(date_max),
        network_id=network.code,
        trading_offset=trading_offset,
        network_interval_size="1 hour",
        intervals_per_hour=network.intervals_per_hour,
    )

    return dedent(query)


def run_rooftop_fix() -> None:
    """Fixes overlap in rooftop backfill and backfill"""
    query = sql("delete from at_facility_daily where trading_day < '2018-03-01 00:00:00+00' and network_id='AEMO_ROOFTOP';")

    engine = get_database_engine()

    with engine.begin() as c:
        logger.debug(query)

        if not settings.dry_run:
            c.execute(query)


def exec_aggregates_facility_daily_query(date_min: datetime, date_max: datetime, network: NetworkSchema) -> Any:
    """Executes the facility daily aggregate query for a date range and network"""
    engine = get_database_engine()
    result = None

    logger.info(f"Running for {network.code}  for {date_min} => {date_max}")

    # @TODO should put this check everywhere
    # or place it all in a schema that validates
    if date_max < date_min:
        raise AggregateFacilityDailyException(
            f"exec_aggregates_facility_daily_query: date_max ({date_max}) is prior to date_min ({date_min})"
        )

    query = aggregates_facility_daily_query(date_min=date_min, date_max=date_max, network=network)

    with engine.begin() as c:
        logger.debug(query)

        if not settings.dry_run:
            result = c.execute(sql(query))

    # @NOTE rooftop fix for double counts
    if not settings.dry_run and network is NetworkAEMORooftop:
        run_rooftop_fix()

    return result


def run_aggregates_facility_for_interval(interval: datetime, network: NetworkSchema | None = None, offset: int = 1) -> int | None:
    """Runs and stores emission flows for a particular interval"""

    if not network:
        network = NetworkNEM

    date_end = interval
    date_start = interval.replace(hour=0, minute=0, second=0, microsecond=0)

    return exec_aggregates_facility_daily_query(date_start, date_end, network=network)


def run_facility_aggregates_for_latest_interval(network: NetworkSchema) -> None:
    """Runs facility aggregates for the latest interval"""
    interval = get_last_completed_interval_for_network(network=network)

    if not interval:
        raise Exception("No latest interval found")

    run_aggregates_facility_for_interval(interval, network=network)


def run_aggregates_facility_year(year: int, network: NetworkSchema, run_by_month: int = True) -> None:
    """Run aggregates for a single year

    Args:
        year (int, optional): [description]. Defaults to DATE_CURRENT_YEAR.
        network (NetworkSchema, optional): [description]. Defaults to NetworkNEM.
    """
    today = get_today_opennem()

    # First day of year we want to do _last_ year
    if today.date() == date(year, 1, 1):
        year -= 1

    date_min, date_max = get_aggregate_year_range(year, network=network)
    logger.info(f"Running for year {year} - range : {date_min} {date_max}")

    if not run_by_month:
        exec_aggregates_facility_daily_query(date_min, date_max, network)
        return None

    # Run by month
    month_min = date_min.month
    month_max = 12  # @NOTE make this a param so we can run custom ranges

    if year == today.year:
        month_max = today.month

    for month in range(month_min, month_max + 1):
        date_min, date_max = get_aggregate_month_range(year, month, network=network)

        logger.info(f"Running for month {month} - range : {date_min} {date_max}")

        if not settings.dry_run:
            exec_aggregates_facility_daily_query(date_min, date_max, network)


def run_aggregate_facility_all_by_year(network: NetworkSchema, run_by_month: int = False) -> None:
    """Runs the facility aggregate for a network for all years in its range

    :param network: Network to run for
    :type network: NetworkSchema
    :param run_by_month: Run by month, defaults to True
    :type run_by_month: bool, optional
    """
    if not network.data_first_seen:
        raise AggregateFacilityDailyException(f"Require a network and with data_first_seen: {network.code}")

    year_min = network.data_first_seen.year
    year_max = get_today_opennem().year

    for year in range(year_max, year_min - 1, -1):
        if not run_by_month:
            run_aggregates_facility_year(year=year, network=network)
            continue

        for month in range(1, 13):
            date_min, date_max = get_aggregate_month_range(year, month, network=network)
            logger.info(f"Running for year {year} month {month} - range : {date_min} {date_max}")

            exec_aggregates_facility_daily_query(date_min, date_max, network)


def run_aggregate_facility_days(days: int = 1, network: NetworkSchema | None = None) -> None:
    """Run energy sum update for yesterday. This task is scheduled
    in scheduler/db"""

    if not network or not network.data_first_seen:
        raise AggregateFacilityDailyException("Require a network and with data_first_seen")

    # This is Sydney time as the data is published in local time
    # today_midnight in NEM time
    date_max = get_today_opennem().replace(minute=0, second=0, microsecond=0)
    date_min = (date_max - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

    exec_aggregates_facility_daily_query(date_min, date_max, network)


def run_aggregate_facility_daily_all(networks: list[NetworkSchema]) -> None:
    """Runs the facility aggregate for all networks for all years in its range"""
    if not networks:
        networks = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop, NetworkOpenNEMRooftopBackfill]

    for network in networks:
        if not network.data_first_seen:
            raise Exception(f"Require data first seen for network {network.code}")

        date_min = network.data_first_seen
        date_max = get_last_completed_interval_for_network(network=network)

        if network.data_last_seen:
            date_max = network.data_last_seen

        logger.info(f"Running {network.code} range : {date_min} {date_max}")

        exec_aggregates_facility_daily_query(date_min=date_min, date_max=date_max, network=network)


# debug entry point
if __name__ == "__main__":
    date_min = datetime.fromisoformat("2015-01-01T00:00:00+10:00")
    date_max = datetime.fromisoformat("2016-01-01T00:00:00+10:00")
    network = NetworkNEM
    # exec_aggregates_facility_daily_query(date_min=date_min, date_max=date_max, network=network)
    # run_aggregates_facility_year(year=2015, network=network)
    # for year in range(2004, 2009):
    # run_aggregates_facility_year(network=network, year=year, run_by_month=False)
    # run_aggregate_facility_all_by_year(network=NetworkNEM, run_by_month=True)
    run_aggregates_facility_year(year=2024, network=NetworkNEM, run_by_month=True)
