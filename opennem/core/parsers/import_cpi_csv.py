"""
Import CPI data from RBA CSV file to update the database

This script reads the GCPIAG series from the RBA CPI CSV and updates
the database with any missing values.

Usage:
    uv run -m opennem.core.parsers.import_cpi_csv
"""

import asyncio
import csv
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from opennem.db import get_write_session
from opennem.db.models.opennem import Stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opennem.core.parsers.import_cpi_csv")


async def get_latest_cpi_date() -> datetime | None:
    """Get the most recent CPI date in the database"""
    async with get_write_session() as session:
        result = await session.execute(select(func.max(Stats.stat_date)).where(Stats.stat_type == "CPI", Stats.country == "au"))
        return result.scalar()


async def parse_csv_data(csv_path: Path, after_date: datetime | None = None) -> list[dict]:
    """
    Parse the RBA CSV file and extract GCPIAG series data

    Args:
        csv_path: Path to the CSV file
        after_date: Only include dates after this date (for incremental updates)

    Returns:
        List of dictionaries with stat data
    """
    records = []

    with open(csv_path, encoding="latin-1") as csvfile:
        reader = csv.reader(csvfile)

        # Skip header rows until we find the Series ID row
        series_id_row = None
        row_index = 0
        for row in reader:
            row_index += 1
            if row and row[0] == "Series ID":
                series_id_row = row
                break

        if not series_id_row:
            raise ValueError("Could not find Series ID row in CSV")

        # Find the column index for GCPIAG
        try:
            gcpiag_index = series_id_row.index("GCPIAG")
        except ValueError as e:
            raise ValueError(f"Could not find GCPIAG series in CSV: {e}") from e

        logger.info(f"Found GCPIAG at column {gcpiag_index}")

        # Now read the data rows
        for row in reader:
            if not row or not row[0]:  # Skip empty rows
                continue

            try:
                # First column is the date
                date_str = row[0]
                # Parse date (format is DD/MM/YYYY)
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")

                # Get the CPI value
                cpi_value_str = row[gcpiag_index]
                if not cpi_value_str:  # Skip if no value
                    continue

                cpi_value = float(cpi_value_str)

                # Skip if we already have this date or earlier
                # Remove timezone info from after_date for comparison
                if after_date:
                    after_date_naive = after_date.replace(tzinfo=None) if after_date.tzinfo else after_date
                    if date_obj <= after_date_naive:
                        continue

                records.append(
                    {
                        "stat_date": date_obj,
                        "country": "au",
                        "stat_type": "CPI",
                        "value": round(cpi_value, 4),  # Round to 4 decimal places
                    }
                )

            except (ValueError, IndexError):
                # Skip rows that can't be parsed as dates or don't have values
                continue

    logger.info(f"Parsed {len(records)} new CPI records from CSV")
    return records


async def import_cpi_data(csv_path: Path):
    """
    Main function to import CPI data from CSV

    Args:
        csv_path: Path to the CSV file
    """
    # Get the latest date we have in the database
    latest_date = await get_latest_cpi_date()

    if latest_date:
        logger.info(f"Latest CPI date in database: {latest_date}")
    else:
        logger.info("No existing CPI data in database")

    # Parse the CSV data
    records = await parse_csv_data(csv_path, after_date=latest_date)

    if not records:
        logger.info("No new records to import")
        return 0

    # Sort records by date
    records.sort(key=lambda x: x["stat_date"])

    logger.info(f"Importing {len(records)} new CPI records")
    logger.info(f"Date range: {records[0]['stat_date']} to {records[-1]['stat_date']}")

    # Insert records into database
    async with get_write_session() as session:
        stmt = insert(Stats).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["stat_date", "country", "stat_type"], set_={"value": stmt.excluded.value}
        )

        await session.execute(stmt)
        # Commit is handled by the context manager

    logger.info(f"Successfully imported {len(records)} CPI records")
    return len(records)


async def verify_import():
    """Verify the import by checking the latest values"""
    async with get_write_session() as session:
        # Get the latest 5 CPI values
        result = await session.execute(
            select(Stats.stat_date, Stats.value)
            .where(Stats.stat_type == "CPI", Stats.country == "au")
            .order_by(Stats.stat_date.desc())
            .limit(5)
        )
        records = result.all()

        print("\nLatest CPI values in database after import:")
        for date, value in records:
            print(f"  {date}: {value}")

        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(Stats).where(Stats.stat_type == "CPI", Stats.country == "au")
        )
        total = count_result.scalar()
        print(f"\nTotal CPI records in database: {total}")


async def main():
    """Main entry point"""
    csv_path = Path("data/cpi_data.csv")

    if not csv_path.exists():
        logger.error(f"CSV file not found at {csv_path}")
        logger.info("Please ensure the CPI CSV file is placed at: data/cpi_data.csv")
        return

    # Import the data
    num_imported = await import_cpi_data(csv_path)

    # Verify the import
    if num_imported > 0:
        await verify_import()


if __name__ == "__main__":
    asyncio.run(main())
