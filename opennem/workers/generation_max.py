"""
Get and store maximum generation for each unit and update the metadata field generation_maximum
and generation_maximum_date stored against each unit in the units table.

See: https://github.com/opennem/opennem/issues/461

"""

import logging
from datetime import timedelta

from sqlalchemy import text

from opennem.db import get_write_session
from opennem.schema import network
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.workers.generation_max")


async def _backfill_max_generation_for_units() -> int:
    """
    Get and store maximum generation for each unit and update the metadata field generation_maximum
    and generation_maximum_date stored against each unit in the units table.

    This performs a full backfill of all historical data.

    Returns:
        int: Number of unit records updated
    """
    # First, query to get max generation for each unit
    max_generation_query = text("""
        WITH max_gen AS (
            SELECT
                facility_code,
                generated,
                interval,
                ROW_NUMBER() OVER (PARTITION BY facility_code ORDER BY generated DESC, interval DESC) as rn
            FROM facility_scada
            WHERE
                generated IS NOT NULL
                AND is_forecast = false
                AND generated > 0
        )
        SELECT
            facility_code,
            round(generated::numeric, 4) as max_generation,
            interval as max_generation_interval
        FROM max_gen
        WHERE rn = 1
    """)

    async with get_write_session() as session:
        result = await session.execute(max_generation_query)
        max_gen_records = result.fetchall()

        logger.info(f"Found {len(max_gen_records)} units with max generation data")

        # Update units table separately
        update_count = 0
        for record in max_gen_records:
            update_query = text("""
                UPDATE units
                SET max_generation = :max_generation,
                    max_generation_interval = :max_generation_interval
                WHERE code = :facility_code
            """)

            await session.execute(
                update_query,
                {
                    "facility_code": record.facility_code,
                    "max_generation": record.max_generation,
                    "max_generation_interval": record.max_generation_interval,
                },
            )
            update_count += 1

        await session.commit()
        logger.info(f"Updated {update_count} unit records with max generation data")

        return update_count


async def update_max_generation_for_units(days_since: int | None = 7) -> int:
    """
    Update max generation for each unit checking only recent data (last N days).
    Only updates if the new max generation is greater than the existing stored value.

    This can be run periodically (e.g., weekly) to check for new maximums.

    Args:
        days_since (int): Number of days to look back from the current interval (default: 7)

    Returns:
        int: Number of unit records updated
    """
    current_interval = get_last_completed_interval_for_network(network=network.NetworkNEM, tz_aware=False)

    if days_since:
        start_interval = current_interval - timedelta(days=days_since)
        start_interval_query = "AND interval >= :start_interval"
    else:
        start_interval = None
        start_interval_query = ""

    logger.info(f"Checking max generation from {start_interval} to {current_interval}")

    # Query recent max generation for each unit
    recent_max_query = text(f"""
        WITH max_gen AS (
            SELECT
                facility_code,
                generated,
                interval,
                ROW_NUMBER() OVER (PARTITION BY facility_code ORDER BY generated DESC, interval DESC) as rn
            FROM facility_scada
            WHERE
                generated IS NOT NULL
                AND is_forecast = false
                AND generated > 0
                {start_interval_query}
        )
        SELECT
            facility_code,
            round(generated::numeric, 4) as max_generation,
            interval as max_generation_interval
        FROM max_gen
        WHERE rn = 1
    """)

    # Get current max values from units table
    current_max_query = text("""
        SELECT code, max_generation, max_generation_interval
        FROM units
        WHERE max_generation IS NOT NULL
    """)

    async with get_write_session() as session:
        # Get recent maximums
        recent_result = await session.execute(recent_max_query, {"start_interval": start_interval})
        recent_max_records = {row.facility_code: row for row in recent_result.fetchall()}

        # Get current stored maximums
        current_result = await session.execute(current_max_query)
        current_max_records = {row.code: row for row in current_result.fetchall()}

        logger.info(f"Found {len(recent_max_records)} units with recent data")

        # Compare and update if new max is greater
        update_count = 0
        for facility_code, recent_max in recent_max_records.items():
            current_max = current_max_records.get(facility_code)

            # Update if no existing max OR new max is greater
            should_update = current_max is None or (
                current_max.max_generation is None or float(recent_max.max_generation) > float(current_max.max_generation)
            )

            if should_update:
                update_query = text("""
                    UPDATE units
                    SET max_generation = :max_generation,
                        max_generation_interval = :max_generation_interval
                    WHERE code = :facility_code
                """)

                await session.execute(
                    update_query,
                    {
                        "facility_code": facility_code,
                        "max_generation": recent_max.max_generation,
                        "max_generation_interval": recent_max.max_generation_interval,
                    },
                )
                update_count += 1

                if current_max and current_max.max_generation:
                    logger.info(
                        f"Updated {facility_code}: {current_max.max_generation} MW -> {recent_max.max_generation} MW "
                        f"at {recent_max.max_generation_interval}"
                    )
                else:
                    logger.info(f"Set {facility_code}: {recent_max.max_generation} MW at {recent_max.max_generation_interval}")

        await session.commit()
        logger.info(f"Updated {update_count} unit records")

        return update_count


if __name__ == "__main__":
    import asyncio

    async def test_update():
        # current_interval = get_last_completed_interval_for_network(network=network.NetworkNEM, tz_aware=False)
        # start_date = datetime(2025, 1, 1)
        # days_since = (current_interval - start_date).days

        count = await update_max_generation_for_units(days_since=None)
        logger.info(f"Updated {count} records")

    asyncio.run(test_update())
