import logging
from datetime import datetime

from fastapi import HTTPException

from opennem.api.export.router import api_export_energy_month
from opennem.api.stats.controllers import get_scada_range, stats_factory
from opennem.api.stats.router import (
    energy_network_fueltech_api,
    power_network_fueltech_api,
    price_network_region_api,
)
from opennem.api.stats.schema import DataQueryResult
from opennem.api.time import human_to_interval
from opennem.api.weather.router import station_observations_api
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.exporter.aws import write_to_s3
from opennem.schema.network import NetworkNEM

YEAR_MIN = 2010

logger = logging.getLogger(__name__)


def wem_export_power():
    engine = get_database_engine()

    stat_set = power_network_fueltech_api(
        network_code="WEM",
        network_region="WEM",
        interval="30m",
        period="7d",
        engine=engine,
    )

    weather = station_observations_api(
        station_code="009021",
        interval="30m",
        period="7d",
        network_code="WEM",
        engine=engine,
    )

    price = price_network_region_api(
        engine=engine,
        network_code="WEM",
        network_region_code="WEM",
        interval="30m",
        period="7d",
    )

    # demand = wem_demand()

    stat_set.data = stat_set.data + price.data + weather.data

    POWER_ENDPOINT = "/power/wem.json"

    # @TODO migrate to s3 methods
    byte_count = write_to_s3(POWER_ENDPOINT, stat_set.json(exclude_unset=True))

    logger.info("Wrote {} bytes to {}".format(byte_count, POWER_ENDPOINT))


def wem_export_years():
    engine = get_database_engine()

    for year in range(datetime.now().year, YEAR_MIN - 1, -1):

        stat_set = None

        try:
            stat_set = energy_network_fueltech_api(
                network_code="WEM",
                network_region="WEM",
                interval="1d",
                year=year,
                period="1Y",
                engine=engine,
            )
        except HTTPException as e:
            logger.info(
                "Could not get energy network fueltech for {} {} : {}".format(
                    "WEM", year, e
                )
            )
            continue

        try:
            weather = station_observations_api(
                station_code="009021",
                interval="1d",
                year=year,
                network_code="WEM",
                engine=engine,
                period=None,
            )
            stat_set.data += weather.data
        except HTTPException:
            pass

        try:
            price = price_network_region_api(
                engine=engine,
                network_code="WEM",
                network_region_code="WEM",
                interval="1d",
                period=None,
                year=year,
            )
            stat_set.data += price.data
        except HTTPException:
            pass

        # market_value = wem_market_value_year(year)

        write_to_s3(
            f"/wem/energy/daily/{year}.json", stat_set.json(exclude_unset=True)
        )


def wem_export_all():
    """

        @TODO this is slow atm because of on_energy_sum
    """

    engine = get_database_engine()

    stats = energy_network_fueltech_api(
        network_code="WEM",
        period="all",
        engine=engine,
        interval="1M",
        network_region=None,
    )

    try:
        price = price_network_region_api(
            engine=engine,
            network_code="WEM",
            network_region_code="WEM",
            interval="1M",
            period="all",
        )
        stats.data += price.data
    except HTTPException:
        pass
    # market_value = wem_market_value_all()

    write_to_s3("/wem/energy/monthly/all.json", stats.json(exclude_unset=True))


def au_export_power():
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


def wem_run_all():
    wem_export_power()
    wem_export_years()


if __name__ == "__main__":
    # wem_run_all()
    # wem_export_all()
    au_export_power()
