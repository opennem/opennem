"""
Descriptions related methods for all Milestones

"""

import logging

from pydantic import UUID4
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from opennem.api.milestones.queries import get_milestone_record, get_milestone_records
from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.controllers import map_milestone_output_records_from_db, map_milestone_output_schema_to_record
from opennem.recordreactor.utils import get_record_description

logger = logging.getLogger("opennem.recordreactor.descriptions")


async def update_milestone_description(session: AsyncSession, instance_id: UUID4, description: str) -> None:
    """Updates the description of a milestone"""
    update_query = update(Milestones).where(Milestones.instance_id == instance_id)
    await session.execute(update_query.values(description=description))


async def refresh_milestone_descriptions(limit: int | None = None, instance_id: UUID4 | None = None) -> None:
    """Refreshes the milestone descriptions"""

    async with SessionLocal() as session:
        if instance_id:
            record = await get_milestone_record(session=session, instance_id=instance_id)
            if record:
                records = [record]
            else:
                records = []
        else:
            records, _ = await get_milestone_records(session=session, limit=limit)

        logger.info(f"Refreshing {len(records)} milestone descriptions")

        record_schemas = map_milestone_output_records_from_db(records)

        tasks = []

        logger.info(f"Updating {len(record_schemas)} milestone descriptions")

        with tqdm(total=len(record_schemas), desc="Refreshing milestones") as pbar:
            for record in record_schemas:
                record_input = map_milestone_output_schema_to_record(record)
                update_description = get_record_description(record_input)

                tasks.append(
                    update_milestone_description(session=session, instance_id=record.instance_id, description=update_description)
                )

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
