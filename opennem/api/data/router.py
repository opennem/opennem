"""
API router for OpenNEM data endpoints.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_versionizer import api_version

from opennem.api.cache_keys import tiered_key_builder
from opennem.api.data.utils import validate_date_range
from opennem.api.intervals import cap_date_end_to_settled_interval
from opennem.api.queries import AGG_TABLE, QueryType, columnar_supported, get_timeseries_query
from opennem.api.response_cache import cached_json
from opennem.api.schema import std_error_responses
from opennem.api.security import authenticated_user, optional_user
from opennem.api.timeseries import columnar_to_timeseries_response, rows_to_timeseries_response
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import execute_async, get_clickhouse_dependency

router = APIRouter()
logger = logging.getLogger("opennem.api.data")

_SUPPORTED_METRICS = [
    Metric.ENERGY,
    Metric.POWER,
    Metric.EMISSIONS,
    Metric.MARKET_VALUE,
    Metric.STORAGE_BATTERY,
]


@api_version(4)
@router.get("/network/{network_code}", responses=std_error_responses())
@cached_json(expire=60 * 5, live_expire=60, key_builder=tiered_key_builder)
async def get_network_data(
    network_code: Annotated[
        str,
        Path(description="Network identifier — see `/networks` for valid codes.", examples=["NEM"]),
    ],
    metrics: Annotated[
        list[Metric],
        Query(
            description="One or more metrics to return. Multi-value: `?metrics=energy&metrics=power`.",
            examples=[["energy"]],
            min_length=1,
        ),
    ],
    interval: Annotated[
        Interval,
        Query(description="Bucket size for time-series aggregation.", examples=["1h"]),
    ] = Interval.INTERVAL,
    date_start: Annotated[
        datetime | None,
        Query(description="Inclusive start of the query window (network-local time).", examples=["2024-01-01T00:00:00"]),
    ] = None,
    date_end: Annotated[
        datetime | None,
        Query(description="Inclusive end of the query window (network-local time).", examples=["2024-01-02T00:00:00"]),
    ] = None,
    network_region: Annotated[
        str | None,
        Query(description="Restrict to a single network region (price zone).", examples=["NSW1"]),
    ] = None,
    fueltech: Annotated[
        list[str] | None,
        Query(
            description="Restrict to one or more fueltechs (e.g. `coal_black`, `solar_utility`).",
            examples=[["solar_utility"]],
        ),
    ] = None,
    fueltech_group: Annotated[
        list[str] | None,
        Query(description="Restrict to one or more fueltech groups (e.g. `coal`, `renewable`).", examples=[["renewable"]]),
    ] = None,
    primary_grouping: Annotated[
        PrimaryGrouping,
        Query(description="Primary grouping dimension applied to results.", examples=["network_region"]),
    ] = PrimaryGrouping.NETWORK,
    secondary_grouping: Annotated[
        SecondaryGrouping | None,
        Query(description="Optional secondary grouping dimension.", examples=["fueltech_group"]),
    ] = None,
    client: Any = Depends(get_clickhouse_dependency),
    user: optional_user = None,
) -> dict:
    """Get time series data for a network."""
    network = get_api_network_from_code(network_code)
    validate_metrics(metrics, _SUPPORTED_METRICS)

    live_query = date_end is None

    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    if date_start > date_end:
        raise HTTPException(status_code=400, detail="Date start must be before date end")

    # Live request: don't serve the provisional bleeding-edge interval (#575).
    if live_query:
        date_end = await cap_date_end_to_settled_interval(
            client=client, network=network, query_type=QueryType.DATA, date_end=date_end
        )

    secondary_groupings = [secondary_grouping] if secondary_grouping else None

    if network_region:
        primary_grouping = PrimaryGrouping.NETWORK_REGION

    if fueltech:
        secondary_groupings = [SecondaryGrouping.FUELTECH]

    if fueltech_group:
        secondary_groupings = [SecondaryGrouping.FUELTECH_GROUP]

    columnar = columnar_supported(QueryType.DATA, primary_grouping, secondary_groupings)
    query_kwargs: dict[str, Any] = {
        "query_type": QueryType.DATA,
        "network": network,
        "metrics": metrics,
        "interval": interval,
        "date_start": date_start,
        "date_end": date_end,
        "primary_grouping": primary_grouping,
        "secondary_groupings": secondary_groupings,
        "network_region": network_region,
        "fueltech": fueltech,
        "fueltech_group": fueltech_group,
    }
    format_kwargs: dict[str, Any] = {
        "network": network.code,
        "metrics": metrics,
        "interval": interval,
        "primary_grouping": primary_grouping,
        "secondary_groupings": secondary_groupings,
    }

    # Tracker shapes: clickhouse groups rows into series arrays (#740). Any failure in the
    # columnar path falls through to the row path below, which is the reference behaviour.
    if columnar:
        try:
            query, params, column_names = get_timeseries_query(**query_kwargs, columnar=True)
            results = None
            if f" {AGG_TABLE} FINAL" in query:
                # routed to the additive table (#763): any error or empty answer re-runs on unit_intervals
                try:
                    results = await execute_async(client, query, params)
                except Exception as e:
                    logger.warning(f"agg table path failed, using unit_intervals: {e}")
                if not results:
                    results = None
                    query, params, column_names = get_timeseries_query(**query_kwargs, columnar=True, use_agg_table=False)
            if results is None:
                results = await execute_async(client, query, params)
            if not results:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data available for network {network_code} in the specified time range",
                )
            return await asyncio.to_thread(columnar_to_timeseries_response, column_names, results, **format_kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"columnar timeseries path failed, using row path: {e}")

    query, params, column_names = get_timeseries_query(**query_kwargs, use_agg_table=False)

    start_time = time.time()
    try:
        logger.debug(query, params)
        results = await execute_async(client, query, params)
        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(f"Query execution time: {elapsed_ms:.2f} ms")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No data available for network {network_code} in the specified time range",
        )

    return await asyncio.to_thread(rows_to_timeseries_response, column_names, results, **format_kwargs)


@api_version(4)
@router.get("/facilities/{network_code}", responses=std_error_responses())
@cached_json(expire=60 * 5, live_expire=60, key_builder=tiered_key_builder)
async def get_facility_data(
    network_code: Annotated[
        str,
        Path(description="Network identifier — see `/networks` for valid codes.", examples=["NEM"]),
    ],
    metrics: Annotated[
        list[Metric],
        Query(
            description="One or more metrics to return for the requested facilities.",
            examples=[["energy"]],
            min_length=1,
        ),
    ],
    user: authenticated_user,
    interval: Annotated[
        Interval,
        Query(description="Bucket size for time-series aggregation.", examples=["1d"]),
    ] = Interval.INTERVAL,
    facility_code: Annotated[
        list[str] | None,
        Query(
            description="Restrict to one or more facility codes (max 30). Multi-value: repeat the param.",
            examples=[["BANGOWF"]],
            max_length=30,
        ),
    ] = None,
    unit_code: Annotated[
        list[str] | None,
        Query(
            description="Restrict to one or more unit codes (max 30). Multi-value: repeat the param.",
            examples=[["BANGOWF1"]],
            max_length=30,
        ),
    ] = None,
    date_start: Annotated[
        datetime | None,
        Query(description="Inclusive start of the query window (network-local time).", examples=["2024-01-01T00:00:00"]),
    ] = None,
    date_end: Annotated[
        datetime | None,
        Query(description="Inclusive end of the query window (network-local time).", examples=["2024-01-02T00:00:00"]),
    ] = None,
    client: Any = Depends(get_clickhouse_dependency),
) -> dict:
    """Get time series data for a specific facility, grouped by unit."""
    network = get_api_network_from_code(network_code)
    validate_metrics(metrics, _SUPPORTED_METRICS)

    live_query = date_end is None

    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    # Live request: don't serve the provisional bleeding-edge interval (#575).
    if live_query:
        date_end = await cap_date_end_to_settled_interval(
            client=client, network=network, query_type=QueryType.FACILITY, date_end=date_end
        )

    if facility_code and len(facility_code) > 30:
        raise HTTPException(status_code=400, detail="Facility code list must have fewer than 30 entries")

    if unit_code and len(unit_code) > 30:
        raise HTTPException(status_code=400, detail="Unit code list must have fewer than 30 entries")

    query, params, column_names = get_timeseries_query(
        query_type=QueryType.FACILITY,
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        facility_code=facility_code,
        unit_code=unit_code,
    )

    try:
        results = await execute_async(client, query, params)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e

    if not results:
        filter_desc = f"facility={facility_code}" if facility_code else ""
        if unit_code:
            filter_desc += f"{', ' if filter_desc else ''}unit={unit_code}"
        raise HTTPException(
            status_code=404,
            detail=f"No data available for {filter_desc or 'the specified filters'} in the specified time range",
        )

    return await asyncio.to_thread(
        rows_to_timeseries_response,
        column_names,
        results,
        network=network.code,
        metrics=metrics,
        interval=interval,
        primary_grouping=PrimaryGrouping.NETWORK,
        secondary_groupings=None,
        facility_code=facility_code,
    )
