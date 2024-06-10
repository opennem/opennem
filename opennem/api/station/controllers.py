from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from opennem.db.models.opennem import Facility, Station


async def get_stations(
    session: AsyncSession,
    only_approved: bool = True,
    name: str | None = None,
    limit: int | None = None,
    page: int = 1,
) -> list[Station]:
    """
    API controller that gets all stations sorted and joined
    """
    async with session.begin():
        stmt = (
            select(Station)
            .join(Station.facilities)
            .join(Station.location)
            .join(Facility.fueltech)
            .filter(Facility.fueltech_id.isnot(None))
            .filter(Facility.status_id.isnot(None))
        )

        if name:
            stmt = stmt.filter(Station.name.like(f"%{name}%"))
        if only_approved:
            stmt = stmt.filter(Station.approved.is_(True))

        stmt = stmt.order_by(
            Facility.network_region,
            Station.name,
            Facility.network_code,
            Facility.code,
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        stations = result.scalars().unique().all()

    return stations
