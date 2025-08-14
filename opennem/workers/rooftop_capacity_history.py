"""
Worker to import historical rooftop capacity data from APVI into the unit_history table.

This module fetches historical rooftop capacity data from APVI and populates the
unit_history table with capacity_registered values for each rooftop unit.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import polars as pl
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.clients.apvi import get_apvi_rooftop_capacity
from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import Unit

logger = logging.getLogger(__name__)


async def get_unit_mapping(session: AsyncSession) -> dict[str, int]:
    """Get mapping of unit codes to unit IDs for rooftop facilities."""
    query = select(Unit.id, Unit.code).where(Unit.code.like("ROOFTOP_APVI_%"))

    result = await session.execute(query)
    units = result.all()

    # Create mapping of code -> id
    unit_mapping = {unit.code: unit.id for unit in units}

    logger.info(f"Found {len(unit_mapping)} rooftop units in database")

    return unit_mapping


async def bulk_insert_capacity_history(session: AsyncSession, history_records: list[dict[str, Any]]) -> int:
    """Bulk insert capacity history records using raw SQL for performance."""
    if not history_records:
        return 0

    # Insert records one by one, skipping duplicates
    inserted_count = 0

    for record in history_records:
        try:
            # Check if record already exists
            check_query = text("""
                SELECT 1 FROM unit_history
                WHERE unit_id = :unit_id
                AND changed_at = :changed_at
                LIMIT 1
            """)

            result = await session.execute(check_query, {"unit_id": record["unit_id"], "changed_at": record["changed_at"]})

            if result.scalar() is None:
                # Record doesn't exist, insert it
                insert_query = text("""
                    INSERT INTO unit_history (
                        unit_id,
                        changed_at,
                        capacity_registered,
                        changed_by,
                        change_reason
                    ) VALUES (
                        :unit_id,
                        :changed_at,
                        :capacity_registered,
                        :changed_by,
                        :change_reason
                    )
                """)

                await session.execute(insert_query, record)
                inserted_count += 1

        except Exception as e:
            logger.warning(f"Failed to insert record for unit_id={record['unit_id']}, changed_at={record['changed_at']}: {e}")
            continue

    await session.commit()
    return inserted_count


async def import_rooftop_capacity_history() -> None:
    """
    Import historical rooftop capacity data from APVI into unit_history table.

    This function:
    1. Fetches all historical capacity data from APVI
    2. Maps facility codes to unit IDs
    3. Bulk inserts the history records
    """
    logger.info("Starting rooftop capacity history import")

    # Get APVI capacity data
    logger.info("Fetching APVI rooftop capacity data")
    df = await get_apvi_rooftop_capacity()

    if df.is_empty():
        logger.error("No data received from APVI")
        return

    logger.info(f"Received {len(df)} capacity records from APVI")

    async with get_write_session() as session:
        # Get unit ID mapping
        unit_mapping = await get_unit_mapping(session)

        if not unit_mapping:
            logger.error("No rooftop units found in database")
            return

        # Filter dataframe to only include units that exist in our database
        df_filtered = df.filter(pl.col("facility_code").is_in(list(unit_mapping.keys())))

        if df_filtered.is_empty():
            logger.error("No matching units found between APVI data and database")
            return

        logger.info(f"Processing {len(df_filtered)} records for existing units")

        # Convert to list of dicts for bulk insert
        history_records = []

        for row in df_filtered.iter_rows(named=True):
            # Skip records with null or zero capacity
            if not row["capacity_registered"] or row["capacity_registered"] <= 0:
                continue

            history_records.append(
                {
                    "unit_id": unit_mapping[row["facility_code"]],
                    "changed_at": datetime.combine(row["month"], datetime.min.time()),
                    "capacity_registered": round(row["capacity_registered"], 4),  # Round to 4 decimal places
                    "changed_by": "apvi_import",
                    "change_reason": "Historical capacity data import from APVI",
                }
            )

        logger.info(f"Prepared {len(history_records)} history records for insertion")

        # Bulk insert the records
        inserted_count = await bulk_insert_capacity_history(session, history_records)

        logger.info(f"Successfully inserted {inserted_count} capacity history records")


async def get_latest_capacity_for_units(session: AsyncSession, unit_codes: list[str] | None = None) -> dict[str, float]:
    """
    Get the latest capacity_registered value for each unit from the history table.

    Args:
        session: Database session
        unit_codes: Optional list of unit codes to filter by

    Returns:
        Dictionary mapping unit code to latest capacity value
    """
    query = text("""
        SELECT DISTINCT ON (u.code)
            u.code,
            uh.capacity_registered,
            uh.changed_at
        FROM units u
        JOIN unit_history uh ON u.id = uh.unit_id
        WHERE u.code LIKE 'ROOFTOP_APVI_%'
        AND uh.capacity_registered IS NOT NULL
        {filter_clause}
        ORDER BY u.code, uh.changed_at DESC
    """)

    # Add filter clause if unit codes provided
    filter_clause = ""
    params = {}
    if unit_codes:
        filter_clause = "AND u.code = ANY(:unit_codes)"
        params["unit_codes"] = unit_codes

    query_str = str(query).replace("{filter_clause}", filter_clause)

    result = await session.execute(text(query_str), params)
    rows = result.all()

    return {row.code: row.capacity_registered for row in rows}


async def check_rooftop_units() -> None:
    """Check which rooftop units exist in the database."""
    async with get_read_session() as session:
        query = select(Unit.id, Unit.code, Unit.capacity_registered).where(Unit.code.like("ROOFTOP_APVI_%")).order_by(Unit.code)

        result = await session.execute(query)
        units = result.all()

        if not units:
            logger.warning("No rooftop units found in database!")
            logger.info(
                "Expected units: ROOFTOP_APVI_NSW, ROOFTOP_APVI_VIC, ROOFTOP_APVI_QLD, ",
                "ROOFTOP_APVI_SA, ROOFTOP_APVI_WA, ROOFTOP_APVI_TAS, ROOFTOP_APVI_NT",
            )
            return

        logger.info(f"\nFound {len(units)} rooftop units:")
        for unit in units:
            logger.info(f"  - {unit.code} (ID: {unit.id}, Current capacity: {unit.capacity_registered} MW)")


async def view_capacity_history_summary() -> None:
    """View a summary of imported capacity history data."""
    async with get_read_session() as session:
        # Get summary statistics
        summary_query = text("""
            SELECT
                u.code,
                COUNT(uh.id) as history_count,
                MIN(uh.changed_at) as earliest_date,
                MAX(uh.changed_at) as latest_date,
                MIN(uh.capacity_registered) as min_capacity,
                MAX(uh.capacity_registered) as max_capacity
            FROM units u
            LEFT JOIN unit_history uh ON u.id = uh.unit_id
            WHERE u.code LIKE 'ROOFTOP_APVI_%'
            AND uh.capacity_registered IS NOT NULL
            GROUP BY u.code
            ORDER BY u.code
        """)

        result = await session.execute(summary_query)
        summaries = result.all()

        if not summaries:
            logger.info("No capacity history data found")
            return

        logger.info("\nCapacity History Summary:")
        logger.info("-" * 100)
        logger.info(f"{'Unit Code':<20} {'Records':<10} {'Earliest':<12} {'Latest':<12} {'Min MW':<10} {'Max MW':<10}")
        logger.info("-" * 100)

        for summary in summaries:
            logger.info(
                f"{summary.code:<20} {summary.history_count:<10} "
                f"{summary.earliest_date.strftime('%Y-%m-%d') if summary.earliest_date else 'N/A':<12} "
                f"{summary.latest_date.strftime('%Y-%m-%d') if summary.latest_date else 'N/A':<12} "
                f"{summary.min_capacity:<10.2f} {summary.max_capacity:<10.2f}"
            )


async def clean_incorrect_capacity_values() -> None:
    """Clean up ALL rooftop capacity history to start fresh with correct values."""
    async with get_write_session() as session:
        # Delete ALL existing rooftop capacity history
        delete_query = text("""
            DELETE FROM unit_history
            WHERE unit_id IN (
                SELECT id FROM units
                WHERE code LIKE 'ROOFTOP_APVI_%'
            )
        """)

        result = await session.execute(delete_query)
        deleted_count = result.rowcount
        await session.commit()

        logger.info(f"Deleted {deleted_count} rooftop capacity history records")

        # Now re-import with correct values
        logger.info("Re-importing with correct values...")
        await import_rooftop_capacity_history()


async def main():
    """Main entry point for the script."""
    try:
        # First check what units exist
        await check_rooftop_units()

        # Then run the import
        await import_rooftop_capacity_history()
    except Exception as e:
        logger.error(f"Error importing rooftop capacity history: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run the import
    asyncio.run(main())
