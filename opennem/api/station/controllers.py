from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.functions import coalesce, func

from opennem.db.models.opennem import Facility, FacilityScada, Station


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
        subquery = (
            select(
                FacilityScada.facility_code,
                func.first_value(FacilityScada.generated)
                .over(partition_by=FacilityScada.facility_code, order_by=desc(FacilityScada.trading_interval))
                .label("latest_generated"),
            )
            .where(FacilityScada.generated.isnot(None))
            .subquery()
        )

        stmt = (
            select(Station, coalesce(subquery.c.latest_generated, 0).label("latest_generated"))
            .join(Station.facilities)
            .join(Station.location)
            .join(Facility.fueltech)
            .outerjoin(subquery, Facility.code == subquery.c.facility_code)
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
        stations = result.unique().all()

    return stations
