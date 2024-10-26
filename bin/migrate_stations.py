"""
Temporary script to migrate stations from the old schema to the new schema.
"""

import logging

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from opennem.db import get_write_session
from opennem.db.models.opennem import Facility

logger = logging.getLogger("migrate_facilities")


async def update_facility(code: str, network_id: str, network_region: str) -> None:
    async with get_write_session() as session:
        stmt = update(Facility).where(Facility.code == code).values(network_id=network_id, network_region=network_region)
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
            stmt = select(Facility)

            result = await session.execute(stmt)
            facilities = result.scalars().all()

            facilities_without_units = 0
            for facility in facilities:
                if not facility.units:
                    facilities_without_units += 1
                    logger.warning(f"Station {facility.code} has no units {facility.name} {facility.approved}")
                    continue

                network_id = facility.units[0].network_id
                network_region = facility.units[0].network_region

                logger.info(f"Updating {facility.code} - {network_id} - {network_region}")

                if not network_id:
                    raise Exception(f"Station {facility.code} has no network_id {facility.name} {facility.approved}")

                if not network_region:
                    raise Exception(f"Station {facility.code} has no network_region {facility.name} {facility.approved}")

                facility.network_id = network_id
                facility.network_region = network_region

                await update_facility(facility.code, network_id, network_region)

            logger.info(f"Processed {len(facilities)} stations")
            logger.info(f"Found {facilities_without_units} stations without units")

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
