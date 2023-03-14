import logging
from textwrap import dedent

logger = logging.getLogger("opennem.queries.power")


def get_power_by_fueltech_query() -> str:
    """For a network and network region get the power by fueltech"""

    __query = """
    SELECT
        intervals_without_gaps.interval at time zone 'AEST' as trading_interval,
        ft.code,
        coalesce(sum(fs.generated), 0)
    FROM generate_series(
        '2023-03-01T00:00:00+10:00',
        latest_interval_nem() at time zone 'AEST',
        '5 minutes'
    ) as intervals_without_gaps(interval)
    cross join fueltech ft
    left join facility_scada fs on fs.trading_interval = intervals_without_gaps.interval
    left join facility f on f.code = fs.facility_code and ft.code = f.fueltech_id
    where
        ft.code not in ('aggregator_dr', 'aggregator_vpp', 'exports', 'imports', 'interconnector') and
        fs.trading_interval <= latest_interval_nem() at time zone 'AEST' and
        fs.trading_interval >= '2023-03-01T00:00:00+10:00' and
        fs.is_forecast is False and
        f.network_region = 'VIC1'
        nd ft.code in ('pumps')
    group by 1, 2
    order by 1 desc, 2 asc
    """

    query = __query.format()

    logger.debug(dedent(query))

    return query
