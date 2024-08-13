"""
RecordReactor peristence methods
"""

import logging

from sqlalchemy.exc import IntegrityError

from opennem.db import SessionLocalAsync
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneRecordOutputSchema, MilestoneRecordSchema
from opennem.recordreactor.significance import calculate_milestone_significance
from opennem.recordreactor.state import get_current_milestone_state
from opennem.recordreactor.utils import check_milestone_is_new, get_record_description

logger = logging.getLogger("opennem.recordreactor.persistence")


async def persist_milestones(
    milestones: list[MilestoneRecordSchema],
):
    """ """

    milestone_state = await get_current_milestone_state()

    async with SessionLocalAsync() as session:
        for record in milestones:
            milestone_prev: MilestoneRecordOutputSchema | None = None

            if record.record_id in milestone_state:
                milestone_prev = milestone_state[record.record_id]

            if not milestone_prev or check_milestone_is_new(record, milestone_prev):
                if not record.value:
                    continue

                description = get_record_description(record)
                significance = calculate_milestone_significance(record)

                milestone_new = Milestones(
                    record_id=record.record_id,
                    interval=record.interval,
                    aggregate=record.aggregate.value,
                    metric=record.metric.value,
                    period=record.period.value,
                    significance=significance,
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

                    # update state to point to this new milestone
                    milestone_state[record.record_id] = MilestoneRecordOutputSchema(
                        **record.model_dump(),
                        network_id=record.network.code,
                        value_unit=record.unit.value,
                        instance_id=milestone_new.instance_id,
                        significance=significance,
                    )

                    # logger.info(
                    #     f"Added milestone for interval {record.aggregate.value} {record.record_id} with value {record.value}"
                    # )
                except IntegrityError:
                    logger.warning(f"Milestone already exists: {record.record_id} for interval {record.interval}")

        await session.commit()
