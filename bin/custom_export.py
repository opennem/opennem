#!/usr/bin/env python3
"""
Custom export script for OpenNEM facility intervals with fueltech breakdowns.

This script:
1. Executes a large SQL query for 2022-2024 facility interval data
2. Streams results to a CSV file
3. Uploads the result to the OpenNEM S3 bucket

The script generates a CSV containing:
- 30-minute intervals for 2022-2024
- Energy (MWh) and emissions (tCO2e) by fueltech
- Price and demand data
- Import/export flows
- Emissions intensity (tCO2e/MWh)

The results are streamed to avoid memory issues with large datasets.
"""

import asyncio
import csv
import gzip
import logging
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp

import asyncpg

from opennem import settings
from opennem.exporter.storage_bucket import cloudflare_uploader

logger = logging.getLogger(__name__)

QUERY = """
WITH facility_aggregates AS (
  SELECT
    time_bucket('30 minutes', fi.interval) as interval,
    fi.network_region,
    ft.code as fueltech,
    sum(fi.energy) as energy,
    sum(fi.emissions) as emissions
  FROM at_facility_intervals fi
  INNER JOIN fueltech ft ON fi.fueltech_code = ft.code
  WHERE
    fi.network_id in ('NEM', 'AEMO_ROOFTOP') or (fi.network_id in ('WEM', 'APVI') and fi.network_region='WEM')
    AND fi.interval >= $1
    AND fi.interval < $2
  GROUP BY 1, 2, 3
),
prices AS (
  SELECT
    time_bucket('30 minutes', interval) as interval,
    network_region,
    ROUND(avg(price)::numeric, 2) as price,
    ROUND(avg(demand)::numeric, 2) as demand
  FROM balancing_summary
  WHERE
    network_id in ('NEM', 'WEM')
    AND interval >= $1
    AND interval < $2
    AND is_forecast = false
  GROUP BY 1, 2
),
flows AS (
  SELECT
    time_bucket('30 minutes', interval) as interval,
    network_region,
    sum(energy_imports) as imports_energy,
    sum(energy_exports) as exports_energy,
    sum(emissions_imports) as imports_emissions,
    sum(emissions_exports) as exports_emissions
  FROM at_network_flows
  WHERE
    network_id in ('NEM', 'WEM')
    AND interval >= $1
    AND interval < $2
  GROUP BY 1, 2
),
totals AS (
  SELECT
    fa.interval,
    fa.network_region,
    sum(fa.energy) as total_energy,
    sum(fa.emissions) as total_emissions,
    max(f.imports_emissions) as imports_emissions,
    max(f.exports_emissions) as exports_emissions
  FROM facility_aggregates fa
  LEFT JOIN flows f ON fa.interval = f.interval AND fa.network_region = f.network_region
  GROUP BY 1, 2
)
SELECT
  intervals.interval_time as interval,
  fa.network_region,
  COALESCE(p.price, 0) as price,
  COALESCE(p.demand, 0) as demand,
  -- Imports/Exports
  COALESCE(ROUND(f.imports_energy::numeric, 2), 0) as imports_energy,
  COALESCE(ROUND(f.exports_energy::numeric * -1, 2), 0) as exports_energy,
  COALESCE(ROUND(f.imports_emissions::numeric, 2), 0) as imports_emissions,
  COALESCE(ROUND(f.exports_emissions::numeric * -1, 2), 0) as exports_emissions,
  -- Energy by fueltech
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'battery_charging' THEN fa.energy END * -1)::numeric, 2), 0)
    as battery_charging_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'battery_discharging' THEN fa.energy END)::numeric, 2), 0)
    as battery_discharging_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'bioenergy_biogas' THEN fa.energy END)::numeric, 2), 0) as bioenergy_biogas_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'bioenergy_biomass' THEN fa.energy END)::numeric, 2), 0) as bioenergy_biomass_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'coal_black' THEN fa.energy END)::numeric, 2), 0) as coal_black_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'coal_brown' THEN fa.energy END)::numeric, 2), 0) as coal_brown_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'distillate' THEN fa.energy END)::numeric, 2), 0) as distillate_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_ccgt' THEN fa.energy END)::numeric, 2), 0) as gas_ccgt_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_ocgt' THEN fa.energy END)::numeric, 2), 0) as gas_ocgt_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_recip' THEN fa.energy END)::numeric, 2), 0) as gas_recip_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_steam' THEN fa.energy END)::numeric, 2), 0) as gas_steam_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'hydro' THEN fa.energy END)::numeric, 2), 0) as hydro_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'pumps' THEN fa.energy END * -1)::numeric, 2), 0) as pumps_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'solar_utility' THEN fa.energy END)::numeric, 2), 0) as solar_utility_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'solar_rooftop' THEN fa.energy END)::numeric, 2), 0) as solar_rooftop_energy,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'wind' THEN fa.energy END)::numeric, 2), 0) as wind_energy,
  -- Emissions by fueltech
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'bioenergy_biogas' THEN fa.emissions END)::numeric, 2), 0)
    as bioenergy_biogas_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'bioenergy_biomass' THEN fa.emissions END)::numeric, 2), 0)
    as bioenergy_biomass_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'coal_black' THEN fa.emissions END)::numeric, 2), 0) as coal_black_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'coal_brown' THEN fa.emissions END)::numeric, 2), 0) as coal_brown_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'distillate' THEN fa.emissions END)::numeric, 2), 0) as distillate_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_ccgt' THEN fa.emissions END)::numeric, 2), 0) as gas_ccgt_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_ocgt' THEN fa.emissions END)::numeric, 2), 0) as gas_ocgt_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_recip' THEN fa.emissions END)::numeric, 2), 0) as gas_recip_emissions,
  COALESCE(ROUND(max(CASE WHEN fa.fueltech = 'gas_steam' THEN fa.emissions END)::numeric, 2), 0) as gas_steam_emissions,
  -- Emissions intensity calculation (tCO2e/MWh)
  CASE
    WHEN COALESCE(t.total_energy, 0) != 0 THEN
      ROUND((
        (COALESCE(t.total_emissions, 0) + COALESCE(t.imports_emissions, 0) + COALESCE(t.exports_emissions, 0))::numeric /
        NULLIF(t.total_energy, 0)::numeric
      )::numeric, 4)
    ELSE 0
  END as emissions_intensity
FROM (
  SELECT generate_series(
    time_bucket('30 minutes', $1::timestamp),
    time_bucket('30 minutes', $2::timestamp - interval '30 minutes'),
    '30 minutes'::interval
  ) as interval_time
) intervals
CROSS JOIN (SELECT DISTINCT network_region FROM facility_aggregates) regions
LEFT JOIN facility_aggregates fa ON intervals.interval_time = fa.interval AND regions.network_region = fa.network_region
LEFT JOIN prices p ON intervals.interval_time = p.interval AND regions.network_region = p.network_region
LEFT JOIN flows f ON intervals.interval_time = f.interval AND regions.network_region = f.network_region
LEFT JOIN totals t ON intervals.interval_time = t.interval AND regions.network_region = t.network_region
GROUP BY 1, 2, 3, 4,
         f.imports_energy, f.exports_energy,
         f.imports_emissions, f.exports_emissions,
         t.total_energy, t.total_emissions,
         t.imports_emissions, t.exports_emissions
ORDER BY intervals.interval_time, fa.network_region
"""


async def stream_results(conn: asyncpg.Connection, start_date: str, end_date: str) -> AsyncGenerator[tuple, None]:
    """
    Stream query results for a date range to avoid memory issues.

    Args:
        conn: Database connection
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Yields:
        Rows of query results
    """
    async with conn.transaction():
        async for record in conn.cursor(QUERY, start_date, end_date):
            yield record


async def export_intervals() -> str:
    """
    Export facility intervals data to CSV, gzip it and upload to S3.

    The function:
    1. Streams query results year by year
    2. Writes to a temporary CSV file
    3. Compresses the file with gzip
    4. Uploads the compressed file to S3
    5. Cleans up temporary files

    Returns:
        str: The S3 URL of the uploaded file
    """
    start_time = datetime.now()
    logger.info("Starting facility intervals export for 2022-2024")

    # Create temporary directory if it doesn't exist
    tmp_dir = Path(mkdtemp(prefix="opennem_export_"))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    csv_path = tmp_dir / "intervals-fueltechs-2022-24.csv"
    gzip_path = tmp_dir / "intervals-fueltechs-2022-24.csv.gz"

    # Connect to database
    conn = await asyncpg.connect(settings.db_url.replace("+asyncpg", ""))

    try:
        # Open CSV file for writing
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Write headers by getting first row of actual data
            async with conn.transaction():
                # Get first row to get column names
                first_row = await conn.fetch(
                    QUERY,
                    datetime(2024, 1, 1),
                    datetime(2024, 1, 2),
                )
                if not first_row:
                    raise ValueError("No data found for 2024-01-01. Cannot determine column headers.")

                headers = list(first_row[0].keys())
                writer.writerow(headers)

            # Process each year
            for year in range(2022, 2025):
                start_date = datetime(year, 1, 1)
                end_date = datetime(year + 1, 1, 1)

                logger.info(f"Processing year {year}")
                row_count = 0

                # Stream results and write to CSV
                async for record in stream_results(conn, start_date, end_date):
                    writer.writerow(record)
                    row_count += 1

                    if row_count % 10000 == 0:
                        logger.info(f"Processed {row_count:,} rows for {year}")

                logger.info(f"Completed year {year} - {row_count:,} rows")

        # Compress CSV file
        logger.info("Compressing CSV file...")
        with open(csv_path, "rb") as f_in:
            with gzip.open(gzip_path, "wb") as f_out:
                f_out.writelines(f_in)

        # Upload to S3
        file_size = os.path.getsize(gzip_path)
        logger.info(f"Uploading compressed file to S3 ({file_size / 1024 / 1024:.1f}MB)...")

        await cloudflare_uploader.upload_file(
            str(gzip_path),
            "exports/custom/wollemi/intervals-fueltechs-2022-24.csv.gz",
            content_type="application/gzip",
        )

        duration = datetime.now() - start_time
        logger.info(f"Export completed in {duration.total_seconds():.1f}s. Compressed size: {file_size / 1024 / 1024:.1f}MB")

        return f"{cloudflare_uploader.bucket_public_url}exports/custom/wollemi/intervals-fueltechs-2022-24.csv.gz"

    finally:
        await conn.close()
        # Cleanup temporary files
        if csv_path.exists():
            csv_path.unlink()
        if gzip_path.exists():
            gzip_path.unlink()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    url = asyncio.run(export_intervals())
    print(f"\nExport completed. File available at:\n{url}")
