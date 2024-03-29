import logging
from datetime import datetime

from sqlalchemy import select

# from opennem.api.utils import get_query_count
from sqlalchemy.sql import func

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones

logger = logging.getLogger("opennem.api.milestones.queries")


def get_milestone_records(
    limit: int = 100, page_number: int = 1, date_start: datetime | None = None, date_end: datetime | None = None
) -> tuple[list[dict], int]:
    """Get a list of all milestones ordered by date with a limit, pagination and optional significance filter"""
    total_records = 0

    with SessionLocal() as session:
        page_number -= 1

        select_query = select(Milestones)

        if date_start:
            select_query = select_query.where(Milestones.interval >= date_start)

        if date_end and date_start != date_end:
            select_query = select_query.where(Milestones.interval <= date_end)

        if date_end and date_start == date_end:
            select_query = select_query.where(Milestones.interval < date_end)

        total_query = select(func.count()).select_from(select_query)
        total_records = session.scalar(total_query)

        offset = page_number * limit

        select_query = select_query.order_by(Milestones.interval.desc()).limit(limit)

        if offset and offset > 0:
            select_query = select_query.offset(offset)

        query = session.scalars(select_query)
        results = query.all()
        records = []

        for rec in results:
            res_dict = rec.__dict__
            res_dict.pop("_sa_instance_state")
            records.append(res_dict)

    return records, total_records


async def get_total_milestones(date_start: datetime | None = None, date_end: datetime | None = None) -> int:
    """Get total number of milestone records"""
    with SessionLocal() as session:
        select_query = select(Milestones)

        if date_start:
            select_query = select_query.where(Milestones.interval >= date_start)

        if date_end:
            select_query = select_query.where(Milestones.interval <= date_end)

        count_stmt = select(func.count()).select_from(select_query)
        num_records = session.scalar(count_stmt)

    return num_records


# debugger entry point
if __name__ == "__main__":
    get_milestone_records()
