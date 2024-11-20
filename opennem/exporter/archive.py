#!/usr/bin/env python
"""
Export data as parquet files to a bucket

Purpose of this module is to export data as parquet files to a public bucket overnight so that it can be
used for bulk imports in dev.

"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import polars as pl

from opennem.db import db_connect_sync
from opennem.exporter.storage_bucket import cloudflare_uploader
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.exporter.archive")
logger.setLevel(logging.DEBUG)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "archive"

if not OUTPUT_DIR.exists():
    raise Exception(f"Output directory {OUTPUT_DIR} does not exist")


logger.debug(f"Writing to {OUTPUT_DIR}")


@dataclass
class OpenNEMDataExport:
    query: str
    file_name: str


def get_fueltech_generation_query(date_start: datetime, date_end: datetime) -> str:
    return f"""
        select
            fs.interval
            ,fs.network_id
            ,fs.network_region
            ,fs.fueltech_code
            ,sum(fs.generated) as generated_mw
            ,sum(fs.energy) as energy_mwh
        from at_facility_intervals fs
        where
            fs.network_id in ('NEM', 'AEMO_ROOFTOP')
            and fs.interval >= '{date_start}'
            and fs.interval < '{date_end}'
        group by 1, 2, 3, 4
        order by 1 desc, 2, 3, 4
    """.format(date_start=date_start, date_end=date_end)


def get_price_and_demand_data(date_start: datetime, date_end: datetime) -> str:
    return f"""
    select
        bs.interval
        ,bs.network_id
        ,bs.network_region
        ,bs.price
        ,bs.demand
    from mv_balancing_summary bs
    where
        bs.network_id = 'NEM'
        and bs.interval >= '{date_start}'
        and bs.interval < '{date_end}'
    order by 1;
    """.format(date_start=date_start, date_end=date_end)


def get_weather_data(date_start: datetime, date_end: datetime) -> str:
    return f"""
        select
            observation_time as trading_interval,
            fs.station_id as station_id,
            avg(fs.temp_air) as temp_air,
            min(fs.temp_air) as temp_min,
            max(fs.temp_air) as temp_max
        from bom_observation fs
        where
            fs.station_id = '023000'
            and fs.observation_time >= '{date_start}'
            and fs.observation_time < '{date_end}'
        group by 1, 2
        order by 1;
    """


def get_import_export_data(date_start: datetime, date_end: datetime) -> str:
    return f"""
        select
            fs.trading_interval at time zone 'AEST' as trading_interval
            ,case when sum(fs.generated) >= 0 then
                abs(sum(fs.generated))
            else 0 end as exports
            ,case when sum(fs.generated) < 0 then
                abs(sum(fs.generated) )
            else 0 end as imports
        from facility_scada fs
        left join facility f on f.code = fs.facility_code
        where
            1=1
            and f.interconnector is True
            and f.network_id in ('NEM')
            and fs.trading_interval >= '{date_start}'
            and fs.trading_interval < '{date_end}'
        group by 1, f.interconnector_region_to
        order by 1 asc;
    """


def get_pre_dispatch_data(date_start: datetime, date_end: datetime) -> str:
    return """
        select

                fs.trading_interval at time zone 'AEST' as trading_interval
                ,fs.network_id
    """


def run_and_export_query(query: str, filename: str) -> None:
    engine = db_connect_sync()

    logger.debug(dedent(query))

    with engine.connect() as conn:
        df = pl.read_database(query, conn, schema_overrides={})
        logger.debug(f"Loaded data frame for {filename} with {df.shape=}")

        destination_filename = str(OUTPUT_DIR / f"{filename}.parquet")
        df.write_parquet(destination_filename)
        logger.info(f"Wrote to {destination_filename}")


def run_archive_exports() -> None:
    """
    Runs the archive exports
    """
    # start at this morning midnight
    date_end = get_today_opennem().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    # go back 1 year by default
    date_start = date_end.replace(year=date_end.year - 1)

    EXPORTS = [
        OpenNEMDataExport(query=get_fueltech_generation_query(date_start, date_end), file_name="1y_fueltech_generation_data"),
        OpenNEMDataExport(query=get_price_and_demand_data(date_start, date_end), file_name="1y_price_and_demand_data"),
        # OpenNEMDataExport(query=get_weather_data(date_start, date_end), file_name="weather_data"),
        # OpenNEMDataExport(query=get_import_export_data(date_start, date_end), file_name="flow_data"),
    ]

    for export in EXPORTS:
        logger.info(f"Running and exporting {export.file_name}")
        run_and_export_query(export.query, export.file_name)


async def sync_archive_exports() -> None:
    """
    Runs the archive exports
    """
    run_archive_exports()

    BUCKET_UPLOAD_DIRECTORY = "archive/nem/"

    # read the files in the archive directory and upload them to the bucket
    for file in OUTPUT_DIR.glob("*.parquet"):
        await cloudflare_uploader.upload_file(
            str(file),
            BUCKET_UPLOAD_DIRECTORY + str(file.name),
            "text/parquet",
        )


def _test_polars_read() -> None:
    files = [
        "https://data.dev.opennem.org.au/archive/nem/1y_price_and_demand_data.parquet",
        "https://data.dev.opennem.org.au/archive/nem/1y_fueltech_generation_data.parquet",
    ]
    for file in files:
        df = pl.read_parquet(file)
        print(df)


if __name__ == "__main__":
    import asyncio

    asyncio.run(sync_archive_exports())

    _test_polars_read()
