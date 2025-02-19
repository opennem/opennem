"""
Facilities API Router

Handles facility and unit data queries and responses.
"""

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem.api.facilities.schema import FacilityResponse
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.security import authenticated_user
from opennem.db import get_read_session
from opennem.db.models.opennem import Facility
from opennem.schema.unit import UnitFueltechType, UnitStatusType

router = APIRouter()


@router.get(
    "/",
    response_model=APIV4ResponseSchema,
    response_model_exclude_none=True,
    tags=["Facilities"],
    description="Get all approved facilities and their associated units",
)
async def get_facilities(
    user: authenticated_user,
    status_id: list[UnitStatusType] | None = Query(None, description="Filter by unit status(es)"),
    fueltech_id: list[UnitFueltechType] | None = Query(None, description="Filter by unit fuel technology type(s)"),
    network_id: str | None = Query(None, description="Filter by network code"),
    network_region: str | None = Query(None, description="Filter by network region"),
) -> APIV4ResponseSchema:
    """
    Get all approved facilities and their associated approved units.

    Excludes:
    - Unapproved facilities and units
    - Units that are interconnectors
    - Units with fueltech_id of solar_rooftop, battery, imports or exports

    Filters:
    - status_id: Filter by one or more unit statuses (operating, committed, retired)
    - fueltech_id: Filter by one or more unit fuel technology types
    - network_id: Filter by network code
    - network_region: Filter by network region

    Returns:
        FacilitiesResponse: List of facilities and their units sorted by facility name
    """
    async with get_read_session() as session:
        # Build base query for facilities
        stmt = (
            select(Facility)
            .options(selectinload(Facility.units))
            .where(
                Facility.approved == True,  # noqa: E712
            )
        )

        # Add network filters if provided
        if network_id:
            stmt = stmt.where(Facility.network_id == network_id)
        if network_region:
            stmt = stmt.where(Facility.network_region == network_region)

        stmt = stmt.order_by(Facility.code)
        result = await session.execute(stmt)
        facilities = result.scalars().all()

        # Convert enum lists to value lists for comparison
        status_values = [s.value for s in status_id] if status_id else None
        fueltech_values = [f.value for f in fueltech_id] if fueltech_id else None

        # Filter facilities and units based on criteria
        filtered_facilities = []
        for facility in facilities:
            # Filter units
            filtered_units = [
                unit
                for unit in facility.units
                if (
                    unit.approved
                    and not unit.interconnector
                    and unit.fueltech_id not in ["solar_rooftop", "battery", "imports", "exports"]
                    and (status_values is None or unit.status_id in status_values)
                    and (fueltech_values is None or unit.fueltech_id in fueltech_values)
                )
            ]

            # Only include facility if it has valid units after filtering
            if filtered_units:
                facility_response = FacilityResponse(
                    code=facility.code,
                    name=facility.name,
                    network_id=facility.network_id,
                    network_region=facility.network_region,
                    description=facility.description,
                    units=filtered_units,
                )
                filtered_facilities.append(facility_response)

        # Sort facilities by name before returning
        filtered_facilities.sort(key=lambda x: x.name.lower())

        return APIV4ResponseSchema(success=True, data=filtered_facilities, total_records=len(filtered_facilities))
