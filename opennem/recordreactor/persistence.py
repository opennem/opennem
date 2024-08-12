"""
RecordReactor demand methods
"""

import logging

from sqlalchemy.exc import IntegrityError

from opennem.db import SessionLocalAsync
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneRecordSchema, MilestoneSchema
from opennem.recordreactor.state import get_current_milestone_state
from opennem.recordreactor.utils import check_milestone_is_new, get_record_description

logger = logging.getLogger("opennem.recordreactor.persistence")


async def persist_milestones(
    milestones: list[MilestoneSchema],
):
    """ """

    milestone_state = await get_current_milestone_state()

    async with SessionLocalAsync() as session:
        for record in milestones:
            milestone_prev: MilestoneRecordSchema | None = None

            if record.record_id in milestone_state:
                milestone_prev = milestone_state[record.record_id]

            if not milestone_prev or check_milestone_is_new(record, milestone_prev):
                if not record.value:
                    logger.warning(f"No data for {record.record_id}")
                    continue

                description = get_record_description(record)

                milestone_new = Milestones(
                    record_id=record.record_id,
                    interval=record.interval,
                    aggregate=record.aggregate.value,
                    metric=record.metric.value,
                    period=record.period.value,
                    significance=1,
                    value=record.value,
                    value_unit=record.unit.value,
                    network_id=record.network.code,
                    description=description,
                    previous_instance_id=milestone_prev.instance_id if milestone_prev else None,
                )

                if record.network_region:
                    milestone_new.network_region = record.network_region

                if record.fueltech:
                    milestone_new.fueltech_id = record.fueltech.code

                try:
                    milestone_new = await session.merge(milestone_new)
                    await session.flush()

                    logger.debug(f"Added milestone for interval {record.record_id} with instance id {milestone_new.instance_id}")

                    # update state to point to this new milestone
                    milestone_state[record.record_id] = MilestoneRecordSchema(
                        **record.model_dump(),
                        instance_id=milestone_new.instance_id,
                        significance=milestone_new.significance,
                    )

                    logger.info(
                        f"Added milestone for interval {record.aggregate.value} {record.record_id} with value {record.value}"
                    )
                except IntegrityError:
                    logger.warning(f"Milestone already exists: {record.record_id} for interval {record.interval}")

        await session.commit()
