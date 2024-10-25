"""

Facility queries
"""

from sqlalchemy import select

from opennem.db import get_read_session
from opennem.db.models.opennem import Facility, Unit


async def get_facility_by_code(facility_code: str) -> Facility:
    """Get a facility by its code"""

    async with get_read_session() as session:
        query = select(Facility).where(Facility.code == facility_code)
        result = await session.execute(query)
        return result.scalars().one()


async def get_unit_by_code(unit_code: str) -> Unit:
    """Get a unit by its code"""

    async with get_read_session() as session:
        query = select(Unit).where(Unit.code == unit_code)
        result = await session.execute(query)
        return result.scalars().one()
