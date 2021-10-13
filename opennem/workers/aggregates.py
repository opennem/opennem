import logging
import os
from datetime import datetime, timedelta
from textwrap import dedent
from typing import Tuple

from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import ScadaDateRange
from opennem.db import get_database_engine
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import DATE_CURRENT_YEAR

logger = logging.getLogger("opennem.workers.aggregates")

DRY_RUN = os.environ.get("DRY_RUN", False)


def aggregates_facility_daily_query(date_min: datetime, date_max: datetime = None) -> str:
    """This is the query to update the at_facility_daily aggregate"""

    __query = """
    insert into at_facility_daily
        select
            date_trunc('day', fs.trading_interval at time zone n.timezone_database) as trading_day,
            f.network_id,
            f.code as facility_code,
            f.fueltech_id,
            sum(fs.energy) as energy,
            sum(fs.market_value) as market_value,
            sum(fs.emissions) as emissions
        from (
            select
                time_bucket_gapfill('30 minutes', fs.trading_interval) as trading_interval,
                fs.facility_code as code,
                coalesce(sum(fs.eoi_quantity), 0) as energy,
                coalesce(sum(fs.eoi_quantity), 0) * coalesce(max(bsn.price), max(bs.price), 0) as market_value,
                coalesce(sum(fs.eoi_quantity), 0) * coalesce(max(f.emissions_factor_co2), 0) as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            left join balancing_summary bsn on
                bsn.trading_interval - INTERVAL '5 minutes' = fs.trading_interval
                and bsn.network_id = n.network_price
                and bsn.network_region = f.network_region
                and f.network_id = 'NEM'
            left join balancing_summary bs on
                bs.trading_interval = fs.trading_interval
                and bs.network_id = n.network_price
                and bs.network_region = f.network_region
                and f.network_id != 'NEM'
            where
                fs.is_forecast is False
                and fs.trading_interval >= '{date_min}'
                and fs.trading_interval <= '{date_max}'
            group by
                1, 2
        ) as fs
        left join facility f on fs.code = f.code
        left join network n on f.network_id = n.code
        where
            f.fueltech_id is not null
            and fs.trading_interval >= '{date_min}'
            and fs.trading_interval <= '{date_max}'
        group by
            1,
            f.network_id,
            f.code,
            f.fueltech_id
    on conflict (trading_day, network_id, facility_code) DO UPDATE set
        energy = EXCLUDED.energy,
        market_value = EXCLUDED.market_value,
        emissions = EXCLUDED.emissions;
    """

    query = __query.format(
        date_min=date_min,
        date_max=date_max,
    )

    return dedent(query)


def aggregates_network_intervals_query(date_min: datetime, date_max: datetime) -> str:
    """aggregates network intervals query"""

    __query = """
        select
            fs.trading_interval,
            f.code,
            f.fueltech_id,
            f.network_id,
            f.network_region,
            f.interconnector,
            f.interconnector_region_to,
            date_trunc('day', fs.trading_interval at time zone 'AEST') as ti_day_aest,
            date_trunc('month', fs.trading_interval at time zone 'AEST') as ti_month_aest,
            date_trunc('day', fs.trading_interval at time zone 'AWST') as ti_day_awst,
            date_trunc('month', fs.trading_interval at time zone 'AWST') as ti_month_awst,
            round(max(fs.energy), 4) as energy,
            case when max(bs.price_dispatch) >= 0  and min(fs.energy) >= 0 then
                coalesce(
                    round(max(fs.energy) * max(bs.price_dispatch), 4),
                    0.0
                )
            else 0.0
            end as market_value,
            case when min(f.emissions_factor_co2) >= 0  and min(fs.energy) >= 0 then
                coalesce(
                    round(max(fs.energy) * min(f.emissions_factor_co2), 4),
                    0.0
                )
            else 0.0
            end as emissions
        from (
            select
                time_bucket('30 minutes', fs.trading_interval) as trading_interval,
                fs.facility_code,
                fs.network_id,
                round(sum(fs.eoi_quantity), 4) as energy
            from facility_scada fs
            where fs.is_forecast is False
            group by
                1, 2, 3
        ) as fs
            left join facility f on fs.facility_code = f.code
            left join balancing_summary bs on
                bs.trading_interval = fs.trading_interval
                and bs.network_id=f.network_id
                and bs.network_region = f.network_region
        where
            f.fueltech_id is not null
            and fs.trading_interval >= '{date_min}'
            and fs.trading_interval <= '{date_max}'
        group by
            1,
            f.code,
            f.fueltech_id,
            f.network_id,
            f.network_region,
            f.interconnector,
            f.interconnector_region_to
        order by 1 desc
    """

    query = __query.format(
        date_min=date_min,
        date_max=date_max,
    )

    return dedent(query)


def exec_aggregates_facility_daily_query(date_min: datetime, date_max: datetime = None) -> bool:
    resp_code: bool = False
    engine = get_database_engine()
    result = None

    query = aggregates_facility_daily_query(date_min, date_max)

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            result = c.execute(query)

    logger.debug(result)

    # @NOTE rooftop fix for double counts
    run_rooftop_fix()

    return resp_code


def _get_year_range(year: int, network: NetworkSchema = NetworkNEM) -> Tuple[datetime, datetime]:
    """Get a date range for a year with end exclusive"""
    tz = network.get_fixed_offset()

    date_min = datetime(year, 1, 1, 0, 0, 0, 0, tzinfo=tz)
    date_max = datetime(year + 1, 1, 1, 0, 0, 0, 0, tzinfo=tz)

    if year == DATE_CURRENT_YEAR:
        date_max = datetime.now().replace(hour=0, minute=0, second=0, tzinfo=tz) + timedelta(
            days=1
        )

    return date_min, date_max


def run_aggregates_facility_year(
    year: int = DATE_CURRENT_YEAR, network: NetworkSchema = NetworkNEM
) -> None:
    """Run aggregates for a single year

    Args:
        year (int, optional): [description]. Defaults to DATE_CURRENT_YEAR.
        network (NetworkSchema, optional): [description]. Defaults to NetworkNEM.
    """
    date_min, date_max = _get_year_range(year)
    logger.info("Running for year {} - range : {} {}".format(year, date_min, date_max))

    exec_aggregates_facility_daily_query(date_min, date_max)


def run_aggregates_facility_all_by_year() -> None:
    YEAR_MIN = 1998
    YEAR_MAX = DATE_CURRENT_YEAR

    for year in range(YEAR_MAX, YEAR_MIN - 1, -1):
        run_aggregates_facility_year(year)


def run_aggregates_facility_all(network: NetworkSchema) -> None:
    scada_range: ScadaDateRange = get_scada_range(network=network)

    if not scada_range:
        logger.error("Could not find a scada range for {}".format(network.code))
        return None

    exec_aggregates_facility_daily_query(date_min=scada_range.start, date_max=scada_range.end)


def run_aggregate_days(days: int = 1, network: NetworkSchema = NetworkNEM) -> None:
    """Run energy sum update for yesterday. This task is scheduled
    in scheduler/db"""

    tz = network.get_fixed_offset()

    # This is Sydney time as the data is published in local time

    # today_midnight in NEM time
    today = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=tz
    ) + timedelta(days=1)

    date_max = today
    date_min = today - timedelta(days=days)

    exec_aggregates_facility_daily_query(date_min, date_max)


def run_rooftop_fix() -> None:
    query = "delete from at_facility_daily where trading_day < '2018-03-01 00:00:00+00' and network_id='AEMO_ROOFTOP';"

    engine = get_database_engine()

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            c.execute(query)


def run_aggregates_all() -> None:
    for network in [NetworkNEM]:
        run_aggregates_facility_all(network)


# Debug entry point
if __name__ == "__main__":
    run_aggregates_all()
