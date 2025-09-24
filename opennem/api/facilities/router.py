"""
Facilities API Router

Handles facility and unit data queries and responses.
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi_cache.decorator import cache
from fastapi_versionizer import api_version
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem.api.facilities.schema import FacilityResponseSchema, UnitResponseSchema
from opennem.api.facilities.utils import serialize_datetime_specificity, unit_specificity_from_string
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.security import authenticated_user
from opennem.db import get_read_session
from opennem.db.models.opennem import Facility, FuelTech, Unit
from opennem.schema.unit import UnitDispatchType, UnitFueltechGroupType, UnitFueltechType, UnitStatusType

router = APIRouter()
logger = logging.getLogger("opennem.api.facilities")


@api_version(major=4)
@router.get(
    "/",
    response_model_exclude_none=True,
    tags=["Facilities"],
    description="Get all facilities and their associated units",
)
@cache(expire=60 * 15)  # 15 minute cache on facility endpoints
async def get_facilities(
    user: authenticated_user,
    facility_code: list[str] | None = Query(None, description="Filter by facility code(s)"),
    status_id: list[UnitStatusType] | None = Query(None, description="Filter by unit status(es)"),
    fueltech_id: list[UnitFueltechType] | None = Query(None, description="Filter by unit fuel technology type(s)"),
    fueltech_group_id: list[UnitFueltechGroupType] | None = Query(
        None, description="Filter by unit fuel technology group type(s)"
    ),
    network_id: list[str] | None = Query(None, description="Filter by network code(s)"),
    network_region: str | None = Query(None, description="Filter by network region"),
) -> APIV4ResponseSchema:
    """
    Get all facilities and their associated units.

    Excludes:
    - Unapproved facilities and units
    - Units that are interconnectors
    - Units with fueltech_id of solar_rooftop, imports or exports

    Filters:
    - facility_code: Filter by one or more facility codes
    - status_id: Filter by one or more unit statuses (operating, committed, retired)
    - fueltech_id: Filter by one or more unit fuel technology types
    - network_id: Filter by one or more network codes
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

        # If fueltech_group_id is provided, we need to join through Unit and FuelTech tables
        if fueltech_group_id:
            fueltech_group_values = [f.value for f in fueltech_group_id]
            stmt = (
                stmt.join(Unit, Unit.station_id == Facility.id)
                .join(FuelTech, Unit.fueltech_id == FuelTech.code)
                .where(FuelTech.fueltech_group_id.in_(fueltech_group_values))
                .distinct()
            )

        # Add network filters if provided
        if network_id:
            stmt = stmt.where(Facility.network_id.in_(network_id))
        if network_region:
            stmt = stmt.where(Facility.network_region == network_region)
        if facility_code:
            stmt = stmt.where(Facility.code.in_(facility_code))

        stmt = stmt.order_by(Facility.code)
        result = await session.execute(stmt)
        facilities = result.scalars().all()

        # Convert enum lists to value lists for comparison
        status_values = [s.value for s in status_id] if status_id else None
        fueltech_values = [f.value for f in fueltech_id] if fueltech_id else None
        fueltech_group_values = [f.value for f in fueltech_group_id] if fueltech_group_id else None

        # Get fueltech to group mapping if we need to filter by group in memory
        fueltech_groups = {}
        if fueltech_group_values:
            ft_result = await session.execute(select(FuelTech))
            for ft in ft_result.scalars().all():
                if str(ft.fueltech_group_id):
                    fueltech_groups[ft.code] = ft.fueltech_group_id

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
                    and unit.fueltech_id not in ["solar_rooftop", "imports", "exports"]
                    and (status_values is None or unit.status_id in status_values)
                    and (fueltech_values is None or unit.fueltech_id in fueltech_values)
                    and (
                        fueltech_group_values is None
                        or (unit.fueltech_id and fueltech_groups.get(unit.fueltech_id) in fueltech_group_values)
                    )
                )
            ]

            # Only include facility if it has valid units after filtering
            if filtered_units:
                # Extract location coordinates if available
                location_dict = None
                if facility.location is not None:
                    try:
                        # Import here to avoid circular dependency
                        from geoalchemy2.shape import to_shape

                        # Convert PostGIS geometry to shapely shape
                        shape = to_shape(facility.location)  # type: ignore
                        # Use coords to get x,y from Point geometry
                        coords = list(shape.coords)[0]
                        location_dict = {"lat": coords[1], "lng": coords[0]}
                    except Exception as e:
                        # Log but don't fail if geometry conversion fails
                        logger.debug(f"Failed to parse location for {facility.code}: {e}")

                # Create unit response objects from filtered units
                unit_responses = [
                    UnitResponseSchema(
                        code=str(unit.code),
                        fueltech_id=UnitFueltechType(unit.fueltech_id) if unit.fueltech_id else None,
                        status_id=UnitStatusType(unit.status_id) if unit.status_id else None,
                        capacity_registered=unit.capacity_registered,
                        capacity_maximum=unit.capacity_maximum,
                        capacity_storage=unit.capacity_storage,
                        emissions_factor_co2=unit.emissions_factor_co2,
                        data_first_seen=unit.data_first_seen,
                        data_last_seen=unit.data_last_seen,
                        dispatch_type=UnitDispatchType(unit.dispatch_type),
                        commencement_date=unit.commencement_date,
                        closure_date=unit.closure_date,
                        expected_operation_date=unit.expected_operation_date,
                        expected_closure_date=unit.expected_closure_date,
                        construction_start_date=unit.construction_start_date,
                        project_approval_date=unit.project_approval_date,
                        project_lodgement_date=unit.project_approval_lodgement_date,
                        commencement_date_specificity=unit_specificity_from_string(unit.commencement_date_specificity),
                        commencement_date_display=serialize_datetime_specificity(
                            unit.commencement_date, unit.commencement_date_specificity
                        ),
                        closure_date_specificity=unit_specificity_from_string(unit.closure_date_specificity),
                        closure_date_display=serialize_datetime_specificity(unit.closure_date, unit.closure_date_specificity),
                        expected_operation_date_specificity=unit_specificity_from_string(
                            unit.expected_operation_date_specificity
                        ),
                        expected_operation_date_display=serialize_datetime_specificity(
                            unit.expected_operation_date, unit.expected_operation_date_specificity
                        ),
                        expected_closure_date_specificity=unit_specificity_from_string(unit.expected_closure_date_specificity),
                        expected_closure_date_display=serialize_datetime_specificity(
                            unit.expected_closure_date, unit.expected_closure_date_specificity
                        ),
                        construction_start_date_specificity=unit_specificity_from_string(
                            unit.construction_start_date_specificity
                        ),
                        construction_start_date_display=serialize_datetime_specificity(
                            unit.construction_start_date, unit.construction_start_date_specificity
                        ),
                        project_approval_date_specificity=unit_specificity_from_string(unit.project_approval_date_specificity),
                        project_approval_date_display=serialize_datetime_specificity(
                            unit.project_approval_date, unit.project_approval_date_specificity
                        ),
                        created_at=unit.cms_created_at,
                        updated_at=unit.cms_updated_at,
                    )
                    for unit in filtered_units
                ]

                facility_response = FacilityResponseSchema(
                    code=facility.code,
                    name=facility.name,
                    network_id=facility.network_id,
                    network_region=facility.network_region,
                    description=facility.description,
                    npi_id=facility.npi_id,
                    location=location_dict,
                    units=unit_responses,
                    created_at=facility.cms_created_at,
                    updated_at=facility.cms_updated_at,
                )
                filtered_facilities.append(facility_response)

        # Return 416 if no facilities match the filters
        if not filtered_facilities:
            filter_desc = ", ".join(
                filter_str
                for filter_str in [
                    f"facility_codes=[{','.join(facility_code)}]" if facility_code else None,
                    f"network_ids=[{','.join(network_id)}]" if network_id else None,
                    f"network_region={network_region}" if network_region else None,
                    f"status_ids=[{','.join(str(s) for s in status_id)}]" if status_id else None,
                    f"fueltech_ids=[{','.join(str(f) for f in fueltech_id)}]" if fueltech_id else None,
                    f"fueltech_group_ids=[{','.join(str(g) for g in fueltech_group_id)}]" if fueltech_group_id else None,
                ]
                if filter_str is not None
            )
            raise HTTPException(
                status_code=416,
                detail=f"No facilities found matching filters: {filter_desc}",
            )

        # Sort facilities by name before returning
        filtered_facilities.sort(key=lambda x: x.name.lower())

        return APIV4ResponseSchema(success=True, data=filtered_facilities, total_records=len(filtered_facilities))
