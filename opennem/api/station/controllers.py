from sqlalchemy import distinct, select
from sqlalchemy.orm import selectinload

from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Unit


async def get_stations(
    only_approved: bool = True,
    name: str | None = None,
    limit: int | None = None,
    page: int = 1,
) -> list[Facility]:
    async with SessionLocal() as session:
        # Subquery to get distinct station IDs
        subquery = (
            select(distinct(Facility.id).label("station_id"))
            .join(Facility.units)
            .join(Facility.location)
            .join(Unit.fueltech)
            .filter(Unit.fueltech_id.is_not(None))
            .filter(Unit.status_id.is_not(None))
            .filter(Facility.approved.is_(True))
        )

        if name:
            subquery = subquery.filter(Facility.name.ilike(f"%{name}%"))

        # Convert subquery to a proper subquery
        subquery = subquery.subquery()

        # Main query
        stmt = (
            select(Facility)
            .join(subquery, Facility.id == subquery.c.station_id)
            .options(
                selectinload(Facility.units.and_(Unit.include_in_geojson == True)),  # noqa: E712
                selectinload(Facility.location),
            )
            .filter(Facility.approved == True)  # noqa: E712
            .order_by(Facility.name)
        )

        if limit:
            stmt = stmt.offset((page - 1) * limit).limit(limit)

        result = await session.execute(stmt)
        stations = result.scalars().unique().all()

    return stations


if __name__ == "__main__":
    import asyncio

    stations = asyncio.run(get_stations())
    for s in stations:
        print(f"{s.name}: {s.code}")
