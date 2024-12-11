#!/usr/bin/env python
"""
Export data as parquet files to a bucket

Purpose of this module is to export data as parquet files to a public bucket overnight so that it can be
used for bulk imports in dev.

The module streams data directly from the database to the storage bucket using polars and async IO.

Exports:
 * generation and energy data per interval by fueltech for the last year
 * price and demand data per interval for the last year
"""

import io
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from textwrap import dedent

import polars as pl
from humanize import naturalsize

from opennem import settings
from opennem.db import db_connect_sync
from opennem.exporter.storage_bucket import cloudflare_uploader
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_complete_day_for_network

logger = logging.getLogger("opennem.exporter.archive")
logger.setLevel(logging.DEBUG)

_BUCKET_UPLOAD_DIRECTORY = "archive/nem/"


@dataclass
class OpenNEMDataExport:
    query: str
    file_name: str
    time_period: timedelta = timedelta(days=365)
    enabled: bool = True

    @property
    def get_output_url(self) -> str:
        path_parts = [settings.s3_bucket_public_url, _BUCKET_UPLOAD_DIRECTORY, self.file_name]
        dir_path = "/".join([i.lstrip("/").rstrip("/") for i in path_parts])
        full_path = f"{dir_path}.parquet"
        return full_path


# queries for archive exports


def _get_fueltech_generation_query(date_start: datetime, date_end: datetime) -> str:
    return dedent(f"""
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
    """)


def _get_price_and_demand_data_query(date_start: datetime, date_end: datetime) -> str:
    return dedent(f"""
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
    """)


def _get_weather_data_query(date_start: datetime, date_end: datetime) -> str:
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


def _get_import_export_data_query(date_start: datetime, date_end: datetime) -> str:
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


_ARCHIVE_EXPORT_QUERY_MAP = {
    "fueltech_generation": OpenNEMDataExport(query="_get_fueltech_generation_query", file_name="1y_fueltech_generation_data"),
    "price_and_demand": OpenNEMDataExport(query="_get_price_and_demand_data_query", file_name="1y_price_and_demand_data"),
    "weather": OpenNEMDataExport(query="_get_weather_data_query", file_name="1y_weather_data", enabled=False),
    "import_export": OpenNEMDataExport(query="_get_import_export_data_query", file_name="1y_import_export_data", enabled=False),
}


async def _stream_and_upload_query(query_func: Callable[[], str], filename: str) -> int:
    """
    Streams query results directly to parquet format and uploads to bucket

    Args:
        query_func: Function that returns the SQL query to execute
        filename: Name of the output file (without extension)

    Returns:
        float: The size of the file in bytes

    Raises:
        Exception: If database connection or upload fails
    """
    engine = db_connect_sync()
    buffer = io.BytesIO()

    try:
        with engine.connect() as conn:
            query = query_func() if callable(query_func) else query_func
            df = pl.read_database(query, conn, schema_overrides={})
            logger.debug(f"Loaded data frame with {df.shape=}")

            # Write parquet to memory buffer
            df.write_parquet(buffer)
            buffer.seek(0)

            # Upload from memory to bucket
            destination = f"{_BUCKET_UPLOAD_DIRECTORY}{filename}.parquet"
            await cloudflare_uploader.upload_bytes(buffer.getvalue(), destination, "application/octet-stream")
            return len(buffer.getvalue())
    except Exception as e:
        logger.error(f"Failed to process {filename}: {str(e)}")
        raise
    finally:
        buffer.close()


async def sync_archive_exports() -> None:
    """
    Runs the archive exports by streaming data directly to storage

    Raises:
        Exception: If any export fails
    """
    # start at this morning midnight
    date_end = get_last_complete_day_for_network(network=NetworkNEM).replace(tzinfo=None)

    for export in _ARCHIVE_EXPORT_QUERY_MAP.values():
        if not export.enabled:
            logger.info(f"Skipping export {export.file_name} as it is not enabled")
            continue

        logger.info(f"Processing export {export.file_name}")
        date_start = date_end - export.time_period

        if export.query not in globals():
            raise ValueError(f"Query {export.query} not found in globals")

        def get_query(export: OpenNEMDataExport, date_start: datetime, date_end: datetime) -> Callable[[], str]:
            return globals()[export.query](date_start, date_end)

        file_size = await _stream_and_upload_query(get_query(export, date_start, date_end), export.file_name)
        file_size_human = naturalsize(file_size, binary=True)
        logger.info(f"Uploaded {file_size_human} to {export.get_output_url}")


def _test_polars_read() -> None:
    """Test reading parquet files from the bucket"""

    for export in _ARCHIVE_EXPORT_QUERY_MAP.values():
        if not export.enabled:
            logger.info(f"Skipping reading export {export.file_name} as it is not enabled")
            continue

        df = pl.read_parquet(export.get_output_url)
        logger.info(f"Read {export.file_name} from {export.get_output_url} with {df.shape=}")
        print(df)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        await sync_archive_exports()
        _test_polars_read()

    asyncio.run(main())
