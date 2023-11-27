from sqlalchemy import select

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones


def get_milestones(limit: int = 100, page_number: int = 1) -> list[dict]:
    """Get a list of all milestones ordered by date with a limit, pagination and optional significance filter"""
    with SessionLocal() as session:
        page_number -= 1

        select_query = select(Milestones).order_by(Milestones.date.desc()).limit(limit).offset(page_number)

        query = session.scalars(select_query)
        results = query.all()
        records = []

        for rec in results:
            res_dict = rec.__dict__
            res_dict.pop("_sa_instance_state")
            records.append(res_dict)

        return records


if __name__ == "__main__":
    get_milestones()
