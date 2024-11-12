"""
Refresh materialized views in chunks working backwards from current date
"""

import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from opennem.db import get_notransaction_session

logger = logging.getLogger("bin.refresh_views")


async def refresh_views(date_start: date, date_end: date) -> None:
    """
    Refreshes the materialized view for a specific date range

    Args:
        date_start (date): Start date for refresh
        date_end (date): End date for refresh
    """
    async with get_notransaction_session() as session:
        view_name = "mv_facility_scada"
        query = text(f"CALL refresh_continuous_aggregate('{view_name}', '{date_start}', '{date_end}');")
        try:
            # First ensure we're not in a transaction
            await session.execute(text("COMMIT;"))
            # Then execute our refresh
            await session.execute(query)
            logger.info(f"Refreshed view from {date_start} to {date_end}")
        except DBAPIError as e:
            if "ActiveSQLTransactionError" in str(e):
                logger.error("Transaction error occurred. Ensure we're not in a transaction block.")
            raise
        except Exception as e:
            logger.error(f"Error refreshing view for period {date_start} to {date_end}: {str(e)}")
            raise


async def _process_chunk(semaphore: asyncio.Semaphore, date_start: date, date_end: date) -> None:
    """
    Process a single chunk with semaphore control

    Args:
        semaphore (asyncio.Semaphore): Semaphore to control concurrent executions
        date_start (date): Start date for the chunk
        date_end (date): End date for the chunk
    """
    async with semaphore:
        await refresh_views(date_start, date_end)


async def refresh_views_chunked(chunk_size: int = 30, max_concurrent: int = 4) -> None:
    """
    Refreshes materialized views in chunks working backwards from current date to Dec 1999.
    Processes multiple chunks concurrently to improve performance.

    Args:
        chunk_size (int): Number of days to process in each chunk
        max_concurrent (int): Maximum number of concurrent refresh operations
    """
    end_date = date(2024, 11, 11)
    start_date = date(1999, 12, 1)

    # Create chunks
    chunks: list[tuple[date, date]] = []
    current_end = end_date

    while current_end > start_date:
        current_start = current_end - timedelta(days=chunk_size)

        # Ensure we don't go before our target start date
        if current_start < start_date:
            current_start = start_date

        chunks.append((current_start, current_end))
        current_end = current_start - timedelta(days=1)

    # Create semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_concurrent)

    # Create tasks for all chunks
    tasks = [_process_chunk(semaphore, chunk_start, chunk_end) for chunk_start, chunk_end in chunks]

    logger.info(f"Processing {len(chunks)} chunks with max {max_concurrent} concurrent operations")

    try:
        # Execute all tasks and wait for completion
        await asyncio.gather(*tasks)
        logger.info("All chunks processed successfully")
    except Exception as e:
        logger.error(f"Error during parallel processing: {str(e)}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(refresh_views_chunked())
