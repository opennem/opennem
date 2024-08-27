import logging
import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from opennem.db import SessionLocal, get_read_session
from opennem.db.models.opennem import Milestones
from opennem.recordreactor.schema import MilestoneAggregate, MilestoneMetric, MilestonePeriod
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.api.milestones.queries")


async def get_milestone_records(
    session: AsyncSession,
    limit: int | None = 100,
    page_number: int = 1,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
    significance: int | None = None,
    fueltech_id: list[str] | None = None,
    aggregate: MilestoneAggregate | None = None,
    metric: MilestoneMetric | None = None,
    networks: list[NetworkSchema] | None = None,
    network_regions: list[str] | None = None,
    record_filter: list[str] | None = None,
    periods: list[MilestonePeriod] | None = None,
    record_id_filter: str | None = None,
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

    if fueltech_id:
        select_query = select_query.where(Milestones.fueltech_id.in_(fueltech_id))

    if aggregate:
        select_query = select_query.where(Milestones.aggregate == aggregate)

    if metric:
        select_query = select_query.where(Milestones.metric == metric)

    if networks:
        select_query = select_query.where(Milestones.network_id.in_([network.code for network in networks]))
        # and no network regions

    if network_regions:
        select_query = select_query.where(Milestones.network_region.in_(network_regions))
    elif not record_filter:
        select_query = select_query.where(Milestones.network_region == None)  # noqa: E711

    if periods:
        select_query = select_query.where(Milestones.period.in_(periods))

    if record_id:
        select_query = select(Milestones).where(Milestones.record_id == record_id)

    if record_filter:
        for f in record_filter:
            select_query = select_query.where(or_(Milestones.network_id == f, Milestones.network_region == f))

    # select record_id where it regexp matches record_id_filter
    if record_id_filter:
        record_id_filter = record_id_filter.replace("*", "%")
        select_query = select_query.where(Milestones.record_id.ilike(f"{record_id_filter}"))

    total_query = select(func.count()).select_from(select_query.subquery())
    total_records = await session.scalar(total_query)

    select_query = select_query.order_by(Milestones.interval.desc())

    offset: int | None = None

    if limit:
        offset = page_number * limit

    if limit:
        select_query = select_query.limit(limit)

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
        select_query = (
            select(Milestones)
            .where(and_(Milestones.record_id == record.record_id, Milestones.interval < record.interval))
            .order_by(Milestones.interval.desc())
        )
        result = await session.execute(select_query)
        records = result.scalars().all()
        record_dict["history"] = [i.__dict__ for i in records]

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


async def get_milestone_record_ids() -> list[dict]:
    """Get a list of all milestone record ids including the most recent record for each record_id"""

    query = """SELECT DISTINCT ON (record_id)
        record_id,
        interval,
        significance,
        value,
        network_id,
        fueltech_id,
        description,
        period,
        aggregate,
        metric,
        value_unit,
        description_long,
        network_region,
        previous_instance_id
    FROM milestones
    ORDER BY record_id, interval DESC"""

    async with get_read_session() as session:
        result = await session.execute(text(query))
        records = result.fetchall()

        record_list = []
        for record in records:
            record_dict = {
                "record_id": record.record_id,
                "interval": record.interval,
                "significance": record.significance,
                "value": record.value,
                "network_id": record.network_id,
                "fueltech_id": record.fueltech_id,
                "description": record.description,
                "period": record.period,
                "aggregate": record.aggregate,
                "metric": record.metric,
                "value_unit": record.value_unit,
                "description_long": record.description_long,
                "network_region": record.network_region,
                "previous_instance_id": record.previous_instance_id,
            }
            record_list.append(record_dict)

        return record_list


# debugger entry point
async def main():
    async with SessionLocal() as session:
        records, total = await get_milestone_records(session)
        print(f"Total records: {total}")
        print(f"First record: {records[0] if records else None}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(get_milestone_record_ids())
