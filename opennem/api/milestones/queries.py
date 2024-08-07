import logging
import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric, MilestonePeriod
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.api.milestones.queries")


async def get_milestone_records(
    session: AsyncSession,
    limit: int = 100,
    page_number: int = 1,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    significance: int | None = None,
    fueltech: list[str] | None = None,
    aggregate: MilestoneAggregate | None = None,
    metric: MilestoneMetric | None = None,
    networks: list[NetworkSchema] | None = None,
    network_regions: list[str] | None = None,
    periods: list[MilestonePeriod] | None = None,
    record_id: str | None = None,
) -> tuple[list[dict], int]:
    """Get a list of all milestones ordered by date with a limit, pagination and optional significance filter"""
    page_number -= 1

    select_query = select(Milestones)

    if date_start:
        select_query = select_query.where(Milestones.interval >= date_start)

    if date_end and date_start != date_end:
        select_query = select_query.where(Milestones.interval <= date_end)

    if date_end and date_start == date_end:
        select_query = select_query.where(Milestones.interval < date_end)

    if significance:
        select_query = select_query.where(Milestones.significance >= significance)

    if fueltech:
        select_query = select_query.where(or_(Milestones.fueltech_group_id.in_(fueltech), Milestones.fueltech_id.in_(fueltech)))

    if aggregate:
        select_query = select_query.where(Milestones.aggregate == aggregate)

    if metric:
        select_query = select_query.where(Milestones.metric == metric)

    if networks:
        select_query = select_query.where(Milestones.network_id.in_([network.code for network in networks]))

    if network_regions:
        select_query = select_query.where(Milestones.network_region.in_(network_regions))

    if periods:
        select_query = select_query.where(Milestones.period.in_(periods))

    if record_id:
        select_query = select_query.where(Milestones.record_id == record_id)

    total_query = select(func.count()).select_from(select_query.subquery())
    total_records = await session.scalar(total_query)

    offset = page_number * limit

    select_query = select_query.order_by(Milestones.interval.desc()).limit(limit)

    if offset and offset > 0:
        select_query = select_query.offset(offset)

    result = await session.execute(select_query)
    results = result.scalars().all()
    records = []

    for rec in results:
        res_dict = rec.__dict__
        res_dict.pop("_sa_instance_state")
        records.append(res_dict)

    return records, total_records


async def get_milestone_record(
    session: AsyncSession,
    instance_id: uuid.UUID,
    include_history: bool = False,
) -> dict | None:
    """Get a single milestone record"""
    select_query = select(Milestones).where(Milestones.instance_id == instance_id)
    result = await session.execute(select_query)
    record = result.scalar_one_or_none()

    if not record:
        return None

    record_dict = record.__dict__

    if include_history:
        # get all the historic records for this milestone based on previous instance ids
        select_query = (
            select(Milestones)
            .where(and_(Milestones.record_id == record.record_id, Milestones.interval < record.interval))
            # .where(Milestones.record_id == record.record_id)
            .order_by(Milestones.interval.desc())
        )
        logger.debug(f"SQL Query: {select_query.compile(compile_kwargs={'literal_binds': True})}")
        result = await session.execute(select_query)
        records = result.scalars().all()
        logger.debug(f"Got {len(records)} historic records")
        record_dict["history"] = records

    return record_dict


async def get_total_milestones(
    session: AsyncSession, date_start: datetime | None = None, date_end: datetime | None = None
) -> int:
    """Get total number of milestone records"""
    select_query = select(Milestones)

    if date_start:
        select_query = select_query.where(Milestones.interval >= date_start)

    if date_end:
        select_query = select_query.where(Milestones.interval <= date_end)

    count_stmt = select(func.count()).select_from(select_query.subquery())
    num_records = await session.scalar(count_stmt)

    return num_records


# debugger entry point
async def main():
    async with SessionLocal() as session:
        records, total = await get_milestone_records(session)
        print(f"Total records: {total}")
        print(f"First record: {records[0] if records else None}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
