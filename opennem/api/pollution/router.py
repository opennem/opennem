"""
Pollution API Router

Handles NPI pollution data queries for facilities.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.routing import serialize_response
from fastapi_versionizer import api_version
from pydantic import TypeAdapter
from sqlalchemy import select

from opennem.api.pollution.cache import build_cache_key, cache_get, cache_set
from opennem.api.schema import APIV4ResponseSchema, std_error_responses
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
_FALLBACK_ADAPTER: TypeAdapter[APIV4ResponseSchema[list[TimeSeries]]] = TypeAdapter(APIV4ResponseSchema[list[TimeSeries]])


@api_version(4)
@router.get(
    "/facilities",
    response_model=APIV4ResponseSchema[list[TimeSeries]],
    response_model_exclude_none=True,
    responses=std_error_responses(),
    tags=["Pollution"],
    description="Get pollution data for facilities with NPI tracking",
)
async def get_facility_pollution(
    request: Request,
    response: Response,
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
) -> Response:
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
    pollutant_codes_to_query = _resolve_pollutant_codes(pollutant_code, pollutant_category)
    key = build_cache_key(facility_code, sorted(pollutant_codes_to_query), date_start, date_end)

    body = await cache_get(key)
    if body is None:
        # HTTPException (404) propagates here, so errors are never cached
        result = await _build_response(facility_code, pollutant_codes_to_query, date_start, date_end)
        body = await _serialize(request, result)
        await cache_set(key, body)

    out = Response(content=body, media_type="application/json")
    # headers set by dependencies (rate limit etc.), as FastAPI appends on the normal path
    out.headers.raw.extend(response.headers.raw)
    return out


def _resolve_pollutant_codes(
    pollutant_code: list[PollutantCode] | None, pollutant_category: list[PollutantCategory] | None
) -> set[str]:
    """Pollutant codes to query: explicit codes plus category members; air pollutants when no filters."""
    codes: set[str] = set()
    if pollutant_code:
        codes.update(code.value for code in pollutant_code)
    if pollutant_category:
        for category in pollutant_category:
            codes.update(code.value for code in get_pollutants_by_category(category))
    if not pollutant_code and not pollutant_category:
        codes.update(code.value for code in get_pollutants_by_category(PollutantCategory.AIR_POLLUTANT))
    return codes


async def _serialize(request: Request, result: APIV4ResponseSchema[list[TimeSeries]]) -> bytes:
    """Serialize exactly as FastAPI's response_model path does (validate + dump_json, exclude_none)."""
    field = getattr(request.scope.get("route"), "response_field", None)
    if field is None:
        return _FALLBACK_ADAPTER.dump_json(result, by_alias=True, exclude_none=True)
    return await serialize_response(field=field, response_content=result, exclude_none=True, dump_json=True)


async def _build_response(
    facility_code: list[str] | None, pollutant_codes_to_query: set[str], date_start: datetime | None, date_end: datetime | None
) -> APIV4ResponseSchema[list[TimeSeries]]:
    async with get_read_session() as session:
        # Build query to get facilities with NPI IDs
        stmt = select(Facility.code, Facility.name, Facility.npi_id).where(
            Facility.approved.is_(True), Facility.npi_id.is_not(None)
        )

        if facility_code:
            stmt = stmt.where(Facility.code.in_(facility_code))

        result = await session.execute(stmt)
        facilities = result.all()

        if not facilities:
            raise HTTPException(
                status_code=404,
                detail=f"No facilities found with NPI tracking for codes: {facility_code}"
                if facility_code
                else "No facilities found with NPI tracking",
            )

        # Get NPI IDs from facilities
        npi_ids = [f.npi_id for f in facilities if f.npi_id]

        # Build query for pollution data
        pollution_stmt = (
            select(
                NPIPollution.npi_facility_id,
                NPIPollution.report_year,
                NPIPollution.pollution_value,
                NPIPollution.data_quality,
                NPISubstance.code,
                NPISubstance.npi_name,
                NPISubstance.category,
                NPISubstance.cas_number,
            )
            .select_from(NPIPollution)
            .join(NPISubstance, NPIPollution.substance_code == NPISubstance.code)
            .join(NPIFacility, NPIPollution.npi_facility_id == NPIFacility.npi_id)
            .where(NPIPollution.npi_facility_id.in_(npi_ids), NPISubstance.enabled.is_(True))
        )

        # Apply pollutant filter if we have specific codes
        if pollutant_codes_to_query:
            pollution_stmt = pollution_stmt.where(NPISubstance.code.in_(list(pollutant_codes_to_query)))

        if date_start:
            pollution_stmt = pollution_stmt.where(NPIPollution.report_year >= date_start.year)

        if date_end:
            pollution_stmt = pollution_stmt.where(NPIPollution.report_year <= date_end.year)

        # category/subcategory tiebreak: several rows can share (facility, substance, year); matches the unique index order
        pollution_stmt = pollution_stmt.order_by(
            NPIPollution.npi_facility_id,
            NPIPollution.substance_code,
            NPIPollution.report_year,
            NPIPollution.pollution_category,
            NPIPollution.pollution_subcategory,
        )

        pollution_result = await session.execute(pollution_stmt)
        pollution_data = pollution_result.all()

        if not pollution_data:
            raise HTTPException(status_code=404, detail="No pollution data available for the specified facilities and time range")

        # Group data by pollutant
        pollutant_groups = defaultdict(lambda: defaultdict(list))

        # Create facility code lookup
        npi_to_facility = {f.npi_id: f.code for f in facilities}
        # first facility wins per code, matching the previous linear `next(...)` lookup
        facility_names: dict[str, str] = {}
        for f in facilities:
            facility_names.setdefault(str(f.code), str(f.name))
        # substance rows already come back from the join; no per-pollutant re-query
        substances: dict[str, Any] = {}

        for row in pollution_data:
            row_facility_code = npi_to_facility.get(row.npi_facility_id, row.npi_facility_id)

            # Create datetime for the report year (use July 1st as middle of reporting year)
            timestamp = datetime(row.report_year, 7, 1)

            # Get data quality or default to unknown
            data_quality = row.data_quality or DataQuality.UNKNOWN.value

            # Add to pollutant group with value and quality
            substances.setdefault(row.code, row)
            pollutant_groups[row.code][row_facility_code].append(
                {"timestamp": timestamp, "value": row.pollution_value, "data_quality": data_quality}
            )

        # Create TimeSeries objects for each pollutant
        timeseries_list = []

        for pollutant_code, facility_data in pollutant_groups.items():
            # Get substance metadata
            substance = substances[str(pollutant_code)]

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
            for fc, data_points in facility_data.items():
                fc_str = str(fc)
                # Sort data points by date
                data_points.sort(key=lambda x: x["timestamp"])

                # Get facility name
                facility_name = facility_names.get(fc_str, fc_str)

                # Format data for TimeSeries (timestamp, value)
                formatted_data = [(dp["timestamp"], dp["value"]) for dp in data_points]

                # Get most common data quality for this series
                quality_counts: dict[str, int] = {}
                for dp in data_points:
                    q = dp["data_quality"]
                    quality_counts[q] = quality_counts.get(q, 0) + 1

                substance_code = str(substance.code)
                result = TimeSeriesResult(
                    name=fc_str,
                    date_start=data_points[0]["timestamp"] if data_points else date_min,
                    date_end=data_points[-1]["timestamp"] if data_points else date_max,
                    columns={
                        "facility_name": facility_name,
                        "pollutant_code": substance_code,
                        "pollutant_label": get_pollutant_label(substance_code),
                        "pollutant_name": str(substance.npi_name),  # Keep for backward compatibility
                        "pollutant_category": str(substance.category),
                        "cas_number": str(substance.cas_number) if substance.cas_number is not None else "",
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
