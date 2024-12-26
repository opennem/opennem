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
from pathlib import Path
from textwrap import dedent

import polars as pl
import psutil
import pyarrow.parquet as pq
from humanize import naturalsize

from opennem import settings
from opennem.core.templates import serve_template
from opennem.db import db_connect_sync
from opennem.exporter.storage_bucket import cloudflare_uploader
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_complete_day_for_network

logger = logging.getLogger("opennem.exporter.archive")
logger.setLevel(logging.DEBUG)

_BUCKET_UPLOAD_DIRECTORY = "archive/nem/"


@dataclass
class OpenNEMDataExport:
    query: Callable[[datetime, datetime, int | None, int | None], str]
    file_name: str
    time_period: timedelta | None = timedelta(days=365)
    enabled: bool = True
    save_local: bool = False

    @property
    def get_output_url(self) -> str:
        path_parts = [settings.s3_bucket_public_url, _BUCKET_UPLOAD_DIRECTORY, self.file_name]
        dir_path = "/".join([i.lstrip("/").rstrip("/") for i in path_parts])
        full_path = f"{dir_path}.parquet"
        return full_path

    @property
    def get_file_name(self) -> str:
        return f"{self.file_name}.parquet"

    @property
    def get_read_path(self) -> str:
        if self.save_local:
            return self.get_file_name

        return self.get_output_url


# queries for archive exports


def _get_fueltech_interval_query(
    date_start: datetime, date_end: datetime, limit: int | None = None, offset: int | None = None
) -> str:
    """
    Get fueltech interval data query with optional pagination.

    Args:
        date_start: Start date for query
        date_end: End date for query
        limit: Optional row limit
        offset: Optional row offset

    Returns:
        str: SQL query string
    """
    query = dedent(f"""
        select
            fs.interval as interval,
            fs.network_id,
            fs.network_region,
            fs.fueltech_code,
            ftg.code as fueltech_group_code,
            ftg.renewable as renewable,
            round(sum(fs.generated)::numeric, 4) as generated,
            round(sum(fs.energy)::numeric, 4) as energy,
            round(sum(fs.emissions)::numeric, 4) as emissions
        FROM at_facility_intervals fs
        JOIN fueltech ft ON ft.code = fs.fueltech_code
        JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
        WHERE
            fs.interval >= '{date_start}'
            and fs.interval < '{date_end}'
        group by 1,2,3,4,5,6
        order by interval desc, network_id, network_region, fueltech_code
    """)

    if limit is not None:
        query += f"\nLIMIT {limit}"
    if offset is not None:
        query += f"\nOFFSET {offset}"

    return query


def _get_fueltech_generation_query(
    date_start: datetime, date_end: datetime, limit: int | None = None, offset: int | None = None
) -> str:
    query = dedent(f"""
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

    if limit is not None:
        query += f"\nLIMIT {limit}"
    if offset is not None:
        query += f"\nOFFSET {offset}"

    return query


def _get_price_and_demand_data_query(
    date_start: datetime, date_end: datetime, limit: int | None = None, offset: int | None = None
) -> str:
    query = dedent(f"""
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
    order by 1
    """)

    if limit is not None:
        query += f"\nLIMIT {limit}"
    if offset is not None:
        query += f"\nOFFSET {offset}"

    return query


def _get_weather_data_query(date_start: datetime, date_end: datetime, limit: int | None = None, offset: int | None = None) -> str:
    query = f"""
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
        order by 1
    """

    if limit is not None:
        query += f"\nLIMIT {limit}"
    if offset is not None:
        query += f"\nOFFSET {offset}"

    return query


def _get_import_export_data_query(
    date_start: datetime, date_end: datetime, limit: int | None = None, offset: int | None = None
) -> str:
    query = f"""
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
        order by 1 asc
    """

    if limit is not None:
        query += f"\nLIMIT {limit}"
    if offset is not None:
        query += f"\nOFFSET {offset}"

    return query


_ARCHIVE_EXPORT_QUERY_MAP = {
    "fueltech_interval_all": OpenNEMDataExport(
        query=_get_fueltech_interval_query,
        time_period=None,
        file_name="fueltech_interval_all",
    ),
    "fueltech_generation": OpenNEMDataExport(
        query=_get_fueltech_generation_query, file_name="1y_fueltech_generation_data", enabled=False
    ),
    "price_and_demand": OpenNEMDataExport(
        query=_get_price_and_demand_data_query, file_name="1y_price_and_demand_data", enabled=False
    ),
    "weather": OpenNEMDataExport(query=_get_weather_data_query, file_name="1y_weather_data", enabled=False),
    "import_export": OpenNEMDataExport(query=_get_import_export_data_query, file_name="1y_import_export_data", enabled=False),
}


def _get_memory_chunk_size() -> int:
    """
    Calculates an appropriate chunk size based on available system memory.

    Returns:
        int: Recommended chunk size for data processing
    """
    # Get available memory in bytes
    available_memory = psutil.virtual_memory().available

    # Use 25% of available memory as a safe buffer
    safe_memory = available_memory * 0.5

    # Estimate row size (adjust based on your data - this assumes 100 bytes per row)
    estimated_row_size = 100

    # Calculate chunk size with a minimum of 10,000 and maximum of 500,000 rows
    chunk_size = int(safe_memory / estimated_row_size)
    return max(10_000, min(500_000, chunk_size))


async def _stream_to_parquet(export_definition: OpenNEMDataExport, buffer: io.BytesIO) -> tuple[int, int]:
    """
    Streams query results directly to parquet format using PyArrow with chunked processing.

    Args:
        query_func: Function that returns SQL query with offset/limit parameters
        buffer: BytesIO buffer to write parquet data to

    Returns:
        tuple[int, int]: Total rows processed and buffer size in bytes

    Raises:
        Exception: If database connection fails
    """
    engine = db_connect_sync()
    chunk_size = _get_memory_chunk_size()

    logger.debug(f"Using chunk size of {chunk_size:,} rows based on available memory")

    # Wrap query func to add offset/limit
    def _get_paginated_query(export_definition: OpenNEMDataExport, offset: int, limit: int) -> str:
        date_start = NetworkNEM.data_first_seen
        date_end = get_last_complete_day_for_network(network=NetworkNEM).replace(tzinfo=None)

        if export_definition.time_period:
            date_start = date_end - export_definition.time_period

        if not date_start:
            raise ValueError(f"Date start for {export_definition.file_name} is not set")

        return export_definition.query(date_start, date_end, limit, offset)

    try:
        with engine.connect() as conn:
            # Get schema from first row
            first_query = _get_paginated_query(export_definition, offset=0, limit=1)

            logger.debug(f"First query: {first_query}")

            first_chunk = pl.read_database(first_query, conn, schema_overrides={})
            schema = first_chunk.to_arrow().schema

            # Create PyArrow writer
            writer = pq.ParquetWriter(buffer, schema, compression="snappy", version="2.6", write_statistics=True)

            # Process chunks
            offset = 0
            total_rows = 0

            while True:
                chunked_query = _get_paginated_query(export_definition, offset, chunk_size)

                logger.debug(f"Chunked query: {chunked_query}")
                df_chunk = pl.read_database(chunked_query, conn, schema_overrides={})

                if df_chunk.height == 0:
                    break

                arrow_table = df_chunk.to_arrow()
                for batch in arrow_table.to_batches():
                    writer.write_batch(batch)
                    total_rows += batch.num_rows

                offset += chunk_size
                logger.debug(f"Processed chunk at offset {offset:,}")

                # if the number of rows is less than the chunk size, we've
                # reached the end of the data and don't need to process any more
                if df_chunk.height < chunk_size:
                    break

            writer.close()
            logger.info(f"Processed total of {total_rows:,} rows")

            buffer.seek(0)
            return total_rows, len(buffer.getvalue())

    except Exception as e:
        logger.error(f"Failed to stream to parquet: {str(e)}")
        raise


async def _stream_and_upload_query(export_definition: OpenNEMDataExport) -> int:
    """
    Streams query results to parquet and uploads to bucket.

    Args:
        query_func: Function that returns the SQL query to execute
        filename: Name of the output file (without extension)

    Returns:
        int: The size of the file in bytes

    Raises:
        Exception: If processing or upload fails
    """
    buffer = io.BytesIO()

    try:
        _, file_size = await _stream_to_parquet(export_definition, buffer)

        # Upload to bucket
        destination = f"{_BUCKET_UPLOAD_DIRECTORY}{export_definition.get_file_name}"
        await cloudflare_uploader.upload_bytes(buffer.getvalue(), destination, "application/octet-stream")

        return file_size

    finally:
        buffer.close()


async def _stream_and_save_query(export_definition: OpenNEMDataExport) -> int:
    """
    Streams query results to parquet and saves locally.

    Args:
        export_definition: The export definition to use

    Returns:
        int: The size of the file in bytes

    Raises:
        Exception: If processing or save fails
    """
    buffer = io.BytesIO()

    try:
        _, file_size = await _stream_to_parquet(export_definition, buffer)

        if export_definition.save_local:
            # Save locally
            output_path = Path(export_definition.get_file_name)
            output_path.write_bytes(buffer.getvalue())
        else:
            # Upload to bucket
            destination = f"{_BUCKET_UPLOAD_DIRECTORY}{export_definition.get_file_name}"
            await cloudflare_uploader.upload_bytes(buffer.getvalue(), destination, "application/octet-stream")

        return file_size

    finally:
        buffer.close()


async def sync_archive_exports(local_save: bool = False) -> None:
    """
    Runs the archive exports by streaming data directly to storage or local files.

    Args:
        local_save: If True, saves files locally instead of uploading to bucket

    Raises:
        Exception: If any export fails
    """

    for export in _ARCHIVE_EXPORT_QUERY_MAP.values():
        if not export.enabled:
            logger.info(f"Skipping export {export.file_name} as it is not enabled")
            continue

        logger.info(f"Processing export {export.file_name}")

        export.save_local = local_save

        file_size = await _stream_and_save_query(export)

        file_size_human = naturalsize(file_size, binary=True)
        logger.info(
            f"{'Saved' if local_save else 'Uploaded'} {file_size_human} "
            f"to {export.get_file_name if local_save else export.get_output_url}"
        )


async def generate_archive_dirlisting() -> None:
    dir_listing = await cloudflare_uploader.list_directory(_BUCKET_UPLOAD_DIRECTORY)

    logger.info(f"Listing {dir_listing.bucket_name} {dir_listing.path}")

    # remove index.html from the dir_listings.files
    dir_listing.files = [file for file in dir_listing.files if file.file_name != "index.html"]

    dirlisting_html = serve_template(template_name="dirlisting.html", **{"directory": dir_listing})

    if isinstance(dirlisting_html, str):
        dirlisting_html = dirlisting_html.encode("utf-8")

    dirlisting_size = await cloudflare_uploader.upload_bytes(
        dirlisting_html, f"{_BUCKET_UPLOAD_DIRECTORY}index.html", "text/html"
    )

    logger.info(f"Uploaded directory listing {naturalsize(dirlisting_size, binary=True)} to {dir_listing.url}")


def _test_polars_read(read_local: bool = False) -> None:
    """Test reading parquet files from the bucket using PyArrow Dataset API"""

    for export in _ARCHIVE_EXPORT_QUERY_MAP.values():
        if read_local:
            export.save_local = True

        if not export.enabled:
            logger.info(f"Skipping reading export {export.file_name} as it is not enabled")
            continue

        logger.info(f"Reading {export.file_name} from {export.get_read_path}")
        df = pl.read_parquet(export.get_read_path)
        logger.debug(f"Read {export.file_name} from {export.get_read_path} with {df.shape=}")
        print(df)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        await sync_archive_exports(local_save=True)
        _test_polars_read(read_local=True)
        # await generate_archive_dirlisting()

    asyncio.run(main())
