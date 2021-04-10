import logging
from datetime import date, datetime, timedelta
from textwrap import dedent
from typing import Optional, Tuple

from opennem.db import get_database_engine
from opennem.utils.dates import DATE_CURRENT_YEAR

logger = logging.getLogger("opennem.workers.aggregates")


def aggregates_facility_daily_query(date_min: date, date_max: Optional[date] = None) -> str:
    """ This is the query to update the at_facility_daily aggregate """

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
                time_bucket('30 minutes', fs.trading_interval) as trading_interval,
                fs.facility_code as code,
                sum(fs.eoi_quantity) as energy,
                sum(fs.eoi_quantity) * coalesce(max(bsn.price), max(bs.price)) as market_value,
                sum(fs.eoi_quantity) * max(f.emissions_factor_co2) as emissions
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
            where fs.is_forecast is False
            group by
                1, 2
        ) as fs
        left join facility f on fs.code = f.code
        left join network n on f.network_id = n.code
        where
            f.fueltech_id is not null
            and fs.trading_interval >= '{date_min}'
            {date_max_query}
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

    date_max_query: str = ""

    if date_max:
        date_max_query = f"and fs.trading_interval <= '{date_max}'"

    query = __query.format(
        date_min=date_min,
        date_max_query=date_max_query,
    )

    return dedent(query)


def exec_aggregates_facility_daily_query(date_min: date, date_max: Optional[date] = None) -> bool:
    resp_code: bool = False
    engine = get_database_engine()

    query = aggregates_facility_daily_query(date_min, date_max)

    with engine.connect() as c:
        logger.debug(query)
        result = c.execute(query)

    logger.debug(result)

    return resp_code


def _get_year_range(year: int) -> Tuple[date, date]:
    date_min = datetime(year, 1, 1).date()
    date_max = datetime(year, 12, 31).date()

    if year == DATE_CURRENT_YEAR:
        date_max = datetime.now().date()

    return date_min, date_max


def run_aggregates_facility_all() -> None:
    YEAR_MIN = 1998
    YEAR_MAX = DATE_CURRENT_YEAR

    for year in range(YEAR_MAX, YEAR_MIN - 1, -1):
        date_min, date_max = _get_year_range(year)
        logger.info("Running for year {} - range : {} {}".format(year, date_min, date_max))

        exec_aggregates_facility_daily_query(date_min, date_max)


if __name__ == "__main__":
    run_aggregates_facility_all()
