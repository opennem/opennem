"""
Descriptions related methods for all Milestones

"""

import logging

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from opennem.api.milestones.queries import get_milestone_records
from opennem.api.milestones.router import map_milestone_output_records_from_db
from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneRecordOutputSchema
from opennem.recordreactor.utils import get_record_description

logger = logging.getLogger("opennem.recordreactor.descriptions")


async def update_milestone_description(session: AsyncSession, milestone: MilestoneRecordOutputSchema, description: str) -> None:
    """Updates the description of a milestone"""
    update_query = update(Milestones).where(Milestones.instance_id == milestone.instance_id)
    await session.execute(update_query.values(description=description))


async def refresh_milestone_descriptions(limit: int | None = None) -> None:
    """Refreshes the milestone descriptions"""

    async with SessionLocal() as session:
        records, total_records = await get_milestone_records(session=session, limit=limit)
        logger.info(f"Refreshing {len(records)} milestone descriptions")

        record_schemas = map_milestone_output_records_from_db(records)

        tasks = []

        logger.info(f"Updating {len(record_schemas)} milestone descriptions")

        with tqdm(total=len(record_schemas), desc="Refreshing milestones") as pbar:
            for record in record_schemas:
                update_description = get_record_description(record)

                tasks.append(update_milestone_description(session, record, update_description))

                if len(tasks) >= 8:
                    await asyncio.gather(*tasks)
                    pbar.update(len(tasks))
                    tasks = []

            # exec remaining tasks
            if tasks:
                await asyncio.gather(*tasks)
                pbar.update(len(tasks))

        await session.commit()

    logger.info(f"Updated {len(record_schemas)} milestone descriptions")


if __name__ == "__main__":
    import asyncio

    asyncio.run(refresh_milestone_descriptions(limit=None))
