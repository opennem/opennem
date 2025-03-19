"""
TimescaleDB Continuous Aggregate Management Module

This module handles the management and refresh of TimescaleDB continuous aggregates
for the OpenNEM platform. It provides functionality to refresh materialized views
and maintain the list of continuous aggregates in the system.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import text

from opennem.db import get_notransaction_session
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.db.views")


class ContinuousAggregate(str, Enum):
    """Enumeration of all continuous aggregates in the system"""

    FUELTECH_DAILY = "mv_fueltech_daily"
    FACILITY_UNIT_DAILY = "mv_facility_unit_daily"
    BALANCING_SUMMARY_HOURLY = "mv_balancing_summary"


async def refresh_continuous_aggregate(
    aggregate_name: ContinuousAggregate,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> None:
    """
    Refresh a specific continuous aggregate for the given time range.

    Args:
        aggregate_name: The name of the continuous aggregate to refresh
        start_date: Start date for the refresh window
        end_date: End date for the refresh window (defaults to current date)
        session: Optional database session to use

    Raises:
        ValueError: If end_date is before start_date
        Exception: If the refresh operation fails
    """

    if start_date and end_date and end_date < start_date:
        raise ValueError("End date must be after start date")

    refresh_sql = text(
        f"CALL refresh_continuous_aggregate('{aggregate_name.value}', '{start_date or 'NULL'}', '{end_date or 'NULL'}')"
    )

    try:
        async with get_notransaction_session() as session_ctx:
            await session_ctx.execute(refresh_sql)
            await session_ctx.commit()

        logger.info(f"Successfully refreshed continuous aggregate {aggregate_name.value} from {start_date} to {end_date}")

    except Exception as e:
        logger.error(f"Failed to refresh continuous aggregate {aggregate_name.value}: {str(e)}")
        raise


async def refresh_all_aggregates(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> None:
    """
    Refresh all continuous aggregates for the given time range.

    Args:
        start_date: Start date for the refresh window
        end_date: End date for the refresh window (defaults to current date)
        session: Optional database session to use

    Raises:
        Exception: If any refresh operation fails
    """

    for aggregate in ContinuousAggregate:
        await refresh_continuous_aggregate(
            aggregate,
            start_date,
            end_date,
        )


async def refresh_recent_aggregates(
    days_back: int = 30,
) -> None:
    """
    Refresh all continuous aggregates for recent data.

    Args:
        hours_back: Number of hours to look back (default 24)
        session: Optional database session to use

    Raises:
        Exception: If any refresh operation fails
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None)
    start_date = (end_date - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)

    await refresh_all_aggregates(start_date, end_date)


if __name__ == "__main__":
    import asyncio

    asyncio.run(refresh_all_aggregates())
