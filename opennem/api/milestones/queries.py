from sqlalchemy import select

from opennem.db import SessionLocal
from opennem.db.models.opennem import Milestones


async def get_milestones(limit: int = 100) -> list[dict]:
    """Get a list of domains"""
    async with SessionLocal() as session:
        select_statement = select(Milestones)

        query = await session.scalars(select_statement)
        results = query.all()
        records = []

        for rec in results:
            res_dict = rec.__dict__
            res_dict.pop("_sa_instance_state")
            records.append(res_dict)

        return records


if __name__ == "__main__":
    import asyncio

    asyncio.run(get_milestones())
