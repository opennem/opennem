from sqlalchemy import distinct, select
from sqlalchemy.orm import selectinload

from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Station


async def get_stations(
    only_approved: bool = True,
    name: str | None = None,
    limit: int | None = None,
    page: int = 1,
) -> list[Station]:
    """
    API controller that gets all approved stations sorted and joined
    """
    async with SessionLocal() as session:
        # Subquery to get distinct station IDs
        subquery = (
            select(distinct(Station.id))
            .join(Station.facilities)
            .join(Station.location)
            .join(Facility.fueltech)
            .filter(Facility.fueltech_id.is_not(None))
            .filter(Facility.status_id.is_not(None))
            .filter(Station.approved.is_(True))
        )

        if name:
            subquery = subquery.filter(Station.name.ilike(f"%{name}%"))

        # Main query
        stmt = (
            select(Station)
            .options(
                selectinload(Station.facilities),
                selectinload(Station.location),
            )
            .filter(Station.id.in_(subquery))
            .order_by(Station.name)
        )

        if limit:
            stmt = stmt.offset((page - 1) * limit).limit(limit)

        result = await session.execute(stmt)
        stations = result.scalars().all()

    return stations


if __name__ == "__main__":
    import asyncio

    stations = asyncio.run(get_stations())
    print(stations)
