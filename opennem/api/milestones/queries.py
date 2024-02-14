import logging
from datetime import datetime

from sqlalchemy import select

# from opennem.api.utils import get_query_count
from sqlalchemy.sql import func

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones

logger = logging.getLogger("opennem.api.milestones.queries")


def get_milestone_records(
    limit: int = 100, page_number: int = 1, date_from: datetime | None = None, date_to: datetime | None = None
) -> list[dict]:
    """Get a list of all milestones ordered by date with a limit, pagination and optional significance filter"""
    with SessionLocal() as session:
        page_number -= 1

        select_query = select(Milestones)

        if date_from:
            select_query = select_query.where(Milestones.interval >= date_from)

        if date_to:
            select_query = select_query.where(Milestones.interval <= date_to)

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

        return records


async def get_total_milestones() -> int:
    """Get total number of milestone records"""
    with SessionLocal() as session:
        select_query = select(Milestones)
        count_stmt = select(func.count()).select_from(select_query)
        num_records = session.scalar(count_stmt)

    return num_records


# debugger entry point
if __name__ == "__main__":
    get_milestone_records()
