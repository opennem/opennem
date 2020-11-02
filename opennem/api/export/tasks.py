import logging
from datetime import datetime

from opennem.api.export.controllers import (
    energy_fueltech_daily,
    power_week,
    weather_daily,
)
from opennem.api.stats.controllers import get_scada_range, stats_factory
from opennem.api.stats.router import price_network_region_api
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.exporter.aws import write_to_s3
from opennem.exporter.local import write_to_local
from opennem.schema.network import NetworkNEM
from opennem.settings import settings

# @TODO q this ..
YEAR_MIN = 2011

logger = logging.getLogger(__name__)


def write_output(
    path: str, stat_set: OpennemDataSet, is_local: bool = False
) -> None:
    write_func = write_to_local if is_local else write_to_s3
    byte_count = write_func(path, stat_set.json(exclude_unset=True))

    logger.info("Wrote {} bytes to {}".format(byte_count, path))


def wem_export_power(is_local: bool = False):
    engine = get_database_engine()

    stat_set = power_week(network_code="WEM")

    stat_set.data += weather_daily(
        station_code="009021",
        network_code="WEM",
        include_min_max=False,
        period_human="7d",
        unit_name="temperature",
    ).data

    price = price_network_region_api(
        engine=engine,
        network_code="WEM",
        network_region_code="WEM",
        interval="30m",
        period="7d",
    )

    stat_set.data = stat_set.data + price.data

    POWER_ENDPOINT = "/power/wem.json"

    write_output(POWER_ENDPOINT, stat_set, is_local=is_local)


def wem_export_daily(limit: int = None, is_local: bool = False):
    processed_years = 0

    for year in range(datetime.now().year, YEAR_MIN - 1, -1):

        stat_set = energy_fueltech_daily(year=year, network_code="WEM")

        weather = weather_daily(
            station_code="009021", year=year, network_code="WEM",
        )
        stat_set.data += weather.data

        write_output(
            f"/wem/energy/daily/{year}.json", stat_set, is_local=is_local
        )

        processed_years += 1

        if limit and limit >= processed_years:
            return None


def wem_export_monthly(is_local: bool = False):
    """

        @TODO this is slow atm because of on_energy_sum (or is it?)
    """

    stat_set = energy_fueltech_daily(network_code="WEM", interval_size="1M")

    stat_set.data += weather_daily(
        station_code="009021", network_code="WEM",
    ).data

    write_output(
        "/wem/energy/monthly/all.json", stat_set, is_local=is_local,
    )


def au_export_power():
    """
        This is shit.
    """
    engine = get_database_engine()

    scada_range = get_scada_range(network=NetworkNEM)
    units = get_unit("power")

    __query = """
        SET SESSION TIME ZONE '+10';

        select
            t.trading_interval,
            sum(t.facility_power),
            t.fueltech_code
        from (
            select
                time_bucket_gapfill('30m', trading_interval) AS trading_interval,
                interpolate(
                    max(fs.generated)
                ) as facility_power,
                fs.facility_code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.trading_interval <= {date_end}
                and fs.trading_interval >= {date_end}::timestamp - '7 days'::interval
                and fs.network_id in ('NEM', 'WEM')
                and f.fueltech_id is not null
            group by 1, 3, 4
        ) as t
        group by 1, 3
        order by 1 desc
    """

    query = __query.format(date_end=scada_range.get_end_sql(),)

    with engine.connect() as c:
        results = list(c.execute(query))

    stats = [
        DataQueryResult(
            interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None
        )
        for i in results
    ]

    interval = human_to_interval("30m")

    stats = stats_factory(
        stats,
        code="au",
        network=NetworkNEM,
        interval=interval,
        units=units,
        fueltech_group=True,
    )

    write_to_s3("/power/au.json", stats.json(exclude_unset=True))


if __name__ == "__main__":
    if settings.env in ["development", "staging"]:
        wem_export_power(is_local=True)
        wem_export_daily(limit=1, is_local=True)
        wem_export_monthly(is_local=True)
    else:
        au_export_power()
        wem_export_power()
        wem_export_daily()
        wem_export_monthly()
