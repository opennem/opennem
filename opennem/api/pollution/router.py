"""
Pollution API Router

Handles NPI pollution data queries for facilities.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi_versionizer import api_version
from sqlalchemy import select

from opennem.api.schema import APIV4ResponseSchema
from opennem.api.security import authenticated_user
from opennem.api.timeseries import TimeSeries, TimeSeriesResult
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db import get_read_session
from opennem.db.models.npi import NPIFacility, NPIPollution, NPISubstance
from opennem.db.models.opennem import Facility
from opennem.schema.pollution import (
    DataQuality,
    PollutantCategory,
    PollutantCode,
    get_pollutant_label,
    get_pollutants_by_category,
)

router = APIRouter()
logger = logging.getLogger("opennem.api.pollution")


@api_version(4)
@router.get(
    "/facilities",
    response_model=APIV4ResponseSchema,
    response_model_exclude_none=True,
    tags=["Pollution"],
    description="Get pollution data for facilities with NPI tracking",
)
async def get_facility_pollution(
    user: authenticated_user,
    facility_code: Annotated[
        list[str] | None, Query(description="The facility code(s) to get pollution data for", examples=["YALLOURN"])
    ] = None,
    pollutant_code: Annotated[
        list[PollutantCode] | None, Query(description="Specific pollutant codes to filter by", examples=[PollutantCode.NOX])
    ] = None,
    pollutant_category: Annotated[
        list[PollutantCategory] | None,
        Query(
            description="Filter by pollutant category(ies). Defaults to 'air_pollutant' if no filters specified",
            examples=[PollutantCategory.AIR_POLLUTANT],
        ),
    ] = None,
    date_start: Annotated[
        datetime | None, Query(description="Start time for the query", examples=["1998-01-01T00:00:00"])
    ] = None,
    date_end: Annotated[datetime | None, Query(description="End time for the query", examples=["2024-12-31T00:00:00"])] = None,
) -> APIV4ResponseSchema:
    """
    Get pollution data for facilities that have NPI tracking.

    This endpoint returns time series pollution data for facilities that are linked to NPI facilities.
    The data includes all tracked pollutants from the National Pollutant Inventory.

    Args:
        facility_code: Optional list of facility codes to filter by
        pollutant_code: Optional list of specific pollutant codes to filter by
        pollutant_category: Optional list of pollutant categories to filter by (defaults to 'air_pollutant' if no filters)
        date_start: Optional start date for the data (defaults to earliest available)
        date_end: Optional end date for the data (defaults to latest available)
        user: Authenticated user

    Returns:
        APIV4ResponseSchema: Time series data response with pollution data grouped by pollutant
    """
    async with get_read_session() as session:
        # Build query to get facilities with NPI IDs
        stmt = select(Facility).where(Facility.approved.is_(True), Facility.npi_id.is_not(None))

        if facility_code:
            stmt = stmt.where(Facility.code.in_(facility_code))

        result = await session.execute(stmt)
        facilities = result.scalars().all()

        if not facilities:
            raise HTTPException(
                status_code=416,
                detail=f"No facilities found with NPI tracking for codes: {facility_code}"
                if facility_code
                else "No facilities found with NPI tracking",
            )

        # Get NPI IDs from facilities
        npi_ids = [f.npi_id for f in facilities if f.npi_id]

        # Build query for pollution data
        pollution_stmt = (
            select(NPIPollution, NPISubstance, NPIFacility)
            .join(NPISubstance, NPIPollution.substance_code == NPISubstance.code)
            .join(NPIFacility, NPIPollution.npi_facility_id == NPIFacility.npi_id)
            .where(NPIPollution.npi_facility_id.in_(npi_ids), NPISubstance.enabled.is_(True))
        )

        # Determine which pollutants to query
        pollutant_codes_to_query = set()

        # If specific codes provided, use those
        if pollutant_code:
            pollutant_codes_to_query.update([code.value for code in pollutant_code])

        # If categories provided, add codes for those categories
        if pollutant_category:
            for category in pollutant_category:
                category_codes = get_pollutants_by_category(category)
                pollutant_codes_to_query.update([code.value for code in category_codes])

        # If no filters provided, default to air pollutants
        if not pollutant_code and not pollutant_category:
            air_codes = get_pollutants_by_category(PollutantCategory.AIR_POLLUTANT)
            pollutant_codes_to_query.update([code.value for code in air_codes])

        # Apply pollutant filter if we have specific codes
        if pollutant_codes_to_query:
            pollution_stmt = pollution_stmt.where(NPISubstance.code.in_(list(pollutant_codes_to_query)))

        if date_start:
            pollution_stmt = pollution_stmt.where(NPIPollution.report_year >= date_start.year)

        if date_end:
            pollution_stmt = pollution_stmt.where(NPIPollution.report_year <= date_end.year)

        pollution_stmt = pollution_stmt.order_by(
            NPIPollution.npi_facility_id, NPIPollution.substance_code, NPIPollution.report_year
        )

        pollution_result = await session.execute(pollution_stmt)
        pollution_data = pollution_result.all()

        if not pollution_data:
            raise HTTPException(status_code=416, detail="No pollution data available for the specified facilities and time range")

        # Group data by pollutant
        pollutant_groups = defaultdict(lambda: defaultdict(list))

        # Create facility code lookup
        npi_to_facility = {f.npi_id: f.code for f in facilities}

        for pollution, substance, _npi_facility in pollution_data:
            facility_code = npi_to_facility.get(pollution.npi_facility_id, pollution.npi_facility_id)

            # Create datetime for the report year (use July 1st as middle of reporting year)
            timestamp = datetime(pollution.report_year, 7, 1)

            # Get data quality or default to unknown
            data_quality = pollution.data_quality or DataQuality.UNKNOWN.value

            # Add to pollutant group with value and quality
            pollutant_groups[substance.code][facility_code].append(
                {"timestamp": timestamp, "value": pollution.pollution_value, "data_quality": data_quality}
            )

        # Create TimeSeries objects for each pollutant
        timeseries_list = []

        for pollutant_code, facility_data in pollutant_groups.items():
            # Get substance metadata
            substance_stmt = select(NPISubstance).where(NPISubstance.code == pollutant_code)
            substance_result = await session.execute(substance_stmt)
            substance = substance_result.scalar_one()

            # Get date range for this pollutant
            all_dates = []
            for _facility_code, data_points in facility_data.items():
                all_dates.extend([dp["timestamp"] for dp in data_points])

            if not all_dates:
                continue

            date_min = min(all_dates)
            date_max = max(all_dates)

            # Create TimeSeriesResult for each facility
            results = []
            for facility_code, data_points in facility_data.items():
                # Sort data points by date
                data_points.sort(key=lambda x: x["timestamp"])

                # Get facility name
                facility_name = next((f.name for f in facilities if f.code == facility_code), facility_code)

                # Format data for TimeSeries (timestamp, value)
                formatted_data = [(dp["timestamp"], dp["value"]) for dp in data_points]

                # Get most common data quality for this series
                quality_counts = {}
                for dp in data_points:
                    q = dp["data_quality"]
                    quality_counts[q] = quality_counts.get(q, 0) + 1

                result = TimeSeriesResult(
                    name=facility_code,
                    date_start=data_points[0]["timestamp"] if data_points else date_min,
                    date_end=data_points[-1]["timestamp"] if data_points else date_max,
                    columns={
                        "facility_name": facility_name,
                        "pollutant_code": substance.code,
                        "pollutant_label": get_pollutant_label(substance.code),
                        "pollutant_name": substance.npi_name,  # Keep for backward compatibility
                        "pollutant_category": substance.category,
                        "cas_number": substance.cas_number or "",
                    },
                    data=formatted_data,
                )
                results.append(result)

            # Create TimeSeries for this pollutant
            timeseries = TimeSeries(
                network_code="AU",  # NPI is Australia-wide
                metric=Metric.POLLUTION,  # We'll need to add this metric
                unit="kg",
                interval=Interval.YEAR,  # NPI data is annual
                date_start=date_min,
                date_end=date_max,
                groupings=["facility", "pollutant"],
                results=results,
            )

            timeseries_list.append(timeseries)

        return APIV4ResponseSchema(data=timeseries_list)
