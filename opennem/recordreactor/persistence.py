"""
RecordReactor peristence methods
"""

import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from opennem.db import get_write_session
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneRecordOutputSchema, MilestoneRecordSchema
from opennem.recordreactor.significance import calculate_milestone_significance
from opennem.recordreactor.state import get_current_milestone_state
from opennem.recordreactor.utils import check_milestone_is_new, get_record_description

logger = logging.getLogger("opennem.recordreactor.persistence")

# PostgreSQL has a limit of 32767 parameters per query
# Each record has 13 fields, so we'll set chunk size to ensure we stay well under the limit
CHUNK_SIZE = 2000  # This gives us max 26000 parameters per query


def _chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def check_and_persist_milestones_chunked(milestones: list[MilestoneRecordSchema]) -> int:
    """
    Persist milestones using bulk insert

    This takes all the milestone records and persists them using a bulk insert operation
    for better performance. Records are processed in chunks to avoid PostgreSQL parameter limits.

    Args:
        milestones: list[MilestoneRecordSchema] - the milestones to persist

    Returns:
        int - the number of records inserted
    """
    if not milestones:
        return 0

    # ensure milestones are sorted from earliest to latest
    milestones = sorted(milestones, key=lambda x: x.interval)

    # Pre-process records into a list of dictionaries for bulk insert
    milestone_records = []

    # get the current milestone state
    milestone_state = await get_current_milestone_state()

    # check for duplicate primary keys
    primary_keys: list[tuple[str, datetime]] = []

    for record in milestones:
        if record.value is None:
            logger.warning(f"Skipping milestone {record.record_id} because it has no value")
            continue

        if record.instance_id is None:
            logger.warning(f"Skipping milestone {record.record_id} because it has no instance_id")
            continue

        # check if the milestone is already in the state
        milestone_prev: MilestoneRecordOutputSchema | None = None

        if record.record_id in milestone_state:
            milestone_prev = milestone_state[record.record_id]

        if milestone_prev and not check_milestone_is_new(record, milestone_prev):
            continue

        # check primary key to make sure we don't have duplicates
        primary_key = (record.record_id, record.interval)

        if primary_key in primary_keys:
            raise ValueError(f"Duplicate primary key: {primary_key}")

        primary_keys.append(primary_key)

        # get the new milestone record details
        description = get_record_description(record)
        significance = calculate_milestone_significance(record)

        milestone_dict = {
            "record_id": record.record_id,
            "instance_id": record.instance_id,
            "interval": record.interval,
            "aggregate": record.aggregate.value,
            "metric": record.metric.value,
            "period": record.period.value,
            "significance": significance,
            "value": round(record.value, 4),
            "value_unit": record.unit.unit,
            "network_id": record.network.code,
            "description": description,
            "previous_instance_id": record.previous_instance_id,
            "network_region": record.network_region if record.network_region else None,
            "fueltech_id": record.fueltech.value if record.fueltech else None,
        }
        milestone_records.append(milestone_dict)

    if not milestone_records:
        return 0

    total_inserted = 0
    async with get_write_session() as session:
        for chunk in _chunks(milestone_records, CHUNK_SIZE):
            stmt = pg_insert(Milestones.__table__).values(chunk)
            stmt = stmt.on_conflict_do_update(
                constraint="excl_milestone_record_id_interval",
                set_={
                    "aggregate": stmt.excluded.aggregate,
                    "metric": stmt.excluded.metric,
                    "period": stmt.excluded.period,
                    "significance": stmt.excluded.significance,
                    "value": stmt.excluded.value,
                    "value_unit": stmt.excluded.value_unit,
                    "network_id": stmt.excluded.network_id,
                    "description": stmt.excluded.description,
                    "previous_instance_id": stmt.excluded.previous_instance_id,
                    "network_region": stmt.excluded.network_region,
                    "fueltech_id": stmt.excluded.fueltech_id,
                },
            )
            try:
                # Process records in chunks

                await session.execute(stmt)
                total_inserted += len(chunk)

            except Exception as e:
                logger.error(f"Error during bulk milestone insertion: {str(e)}")
                # write the records for the current chunk as a csv to a file
                with open(f"milestone_records_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv", "w") as f:
                    for record in chunk:
                        f.write(
                            f"{record['record_id']},{record['instance_id']},{record['interval']},{record['aggregate']},{record['metric']},{record['period']},{record['value']},{record['value_unit']},{record['network_id']},{record['description']},{record['previous_instance_id']},{record['network_region']},{record['fueltech_id']}\n"
                        )

                await session.rollback()
                raise

        await session.commit()
        logger.info(f"Successfully inserted {total_inserted} records")
        return total_inserted


async def check_and_persist_milestones(
    milestones: list[MilestoneRecordSchema],
):
    """
    This checks that the milestone is a record and then persists it if it is

    @TODO: This should be a transaction

    params:
        milestones: list[MilestoneRecordSchema] - the milestones to check and persist

    returns:
        None
    """

    if not milestones:
        return

    # ensure milestones are sorted from earliest to latest
    milestones = sorted(milestones, key=lambda x: x.interval)

    # get the current milestone state
    milestone_state = await get_current_milestone_state()

    async with get_write_session() as session:
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
                    value=round(record.value, 4),
                    value_unit=record.unit.unit,
                    network_id=record.network.code,
                    description=description,
                    previous_instance_id=milestone_prev.instance_id if milestone_prev else None,
                )

                if record.network_region:
                    milestone_new.network_region = record.network_region

                if record.fueltech:
                    milestone_new.fueltech_id = record.fueltech.value

                try:
                    milestone_new = await session.merge(milestone_new)
                    await session.flush()

                    # update state to point to this new milestone
                    milestone_state[record.record_id] = MilestoneRecordOutputSchema(
                        **record.model_dump(exclude={"instance_id", "value_unit", "network_id"}),
                        network_id=record.network.code,
                        value_unit=record.unit.unit,
                        instance_id=milestone_new.instance_id,
                        significance=significance,
                    )

                except IntegrityError:
                    logger.warning(f"Milestone already exists: {record.record_id} for interval {record.interval}")

        await session.commit()
