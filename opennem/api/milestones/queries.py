import logging
import uuid
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric, MilestonePeriods
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
    record_type: MilestoneAggregate | None = None,
    metric: MilestoneMetric | None = None,
    networks: list[NetworkSchema] | None = None,
    network_regions: list[str] | None = None,
    periods: list[MilestonePeriods] | None = None,
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

    if record_type:
        select_query = select_query.where(Milestones.record_type == record_type)

    if metric:
        select_query = select_query.where(Milestones.record_field == metric)

    if networks:
        select_query = select_query.where(Milestones.network_id.in_([network.code for network in networks]))

    if network_regions:
        select_query = select_query.where(Milestones.network_region.in_(network_regions))

    if periods:
        select_query = select_query.where(Milestones.period.in_(periods))

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
) -> dict | None:
    """Get a single milestone record"""
    select_query = select(Milestones).where(Milestones.instance_id == instance_id)
    result = await session.execute(select_query)
    record = result.scalar_one_or_none()

    if not record:
        return None

    logger.debug(record)

    return record.__dict__


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
