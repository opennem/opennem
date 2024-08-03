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
    async with SessionLocal() as session:
        # Subquery to get distinct station IDs
        subquery = (
            select(distinct(Station.id).label("station_id"))
            .join(Station.facilities)
            .join(Station.location)
            .join(Facility.fueltech)
            .filter(Facility.fueltech_id.is_not(None))
            .filter(Facility.status_id.is_not(None))
            .filter(Station.approved.is_(True))
        )

        if name:
            subquery = subquery.filter(Station.name.ilike(f"%{name}%"))

        # Convert subquery to a proper subquery
        subquery = subquery.subquery()

        # Main query
        stmt = (
            select(Station)
            .join(subquery, Station.id == subquery.c.station_id)
            .options(
                selectinload(Station.facilities.and_(Facility.include_in_geojson == True)),  # noqa: E712
                selectinload(Station.location),
            )
            .filter(Station.approved == True)  # noqa: E712
            .order_by(Station.name)
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
