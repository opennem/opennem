"""
Temporary script to migrate stations from the old schema to the new schema.
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from opennem.db import get_write_session
from opennem.db.models.opennem import Station

logger = logging.getLogger("migrate_stations")


async def update_station(code: str, network_id: str, network_region: str) -> None:
    async with get_write_session() as session:
        stmt = update(Station).where(Station.code == code).values(network_id=network_id, network_region=network_region)
        await session.execute(stmt)
        await session.commit()


async def main() -> None:
    """
    Main migration function that loads stations and their facilities using async operations.

    Uses selectinload to eagerly load the facilities relationship to avoid lazy loading issues.
    """
    try:
        async with get_write_session() as session:
            # Use selectinload to eagerly load the facilities relationship
            stmt = select(Station).options(selectinload(Station.facilities))

            result = await session.execute(stmt)
            stations = result.scalars().all()

            stations_without_facilities = 0
            for station in stations:
                if not station.facilities:
                    stations_without_facilities += 1
                    logger.warning(f"Station {station.code} has no facilities {station.name} {station.approved}")
                    continue

                network_id = station.facilities[0].network_id
                network_region = station.facilities[0].network_region

                logger.info(f"Updating {station.code} - {network_id} - {network_region}")

                station.network_id = network_id
                station.network_region = network_region

                await update_station(station.code, network_id, network_region)

            logger.info(f"Processed {len(stations)} stations")
            logger.info(f"Found {stations_without_facilities} stations without facilities")

    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
