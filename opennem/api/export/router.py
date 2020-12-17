from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.param_functions import Query
from starlette import status
from starlette.status import HTTP_501_NOT_IMPLEMENTED

from opennem.api.stats.router import (
    energy_network_fueltech_api,
    power_network_fueltech_api,
    price_network_region_api,
)
from opennem.api.stats.schema import OpennemDataSet
from opennem.api.weather.router import station_observations_api
from opennem.core.networks import network_from_network_code
from opennem.db import get_database_engine
from opennem.schema.network import NetworkSchema

router = APIRouter()

YEAR_CURRENT = datetime.now().date().year


@router.get(
    "/power/wem.json",
    name="Network power",
    response_model_exclude_unset=True,
    response_model=OpennemDataSet,
)
def api_export_power_wem(
    engine: Any = Depends(get_database_engine),
) -> OpennemDataSet:
    stats = power_network_fueltech_api(
        network_code="WEM",
        network_region="WEM",
        interval="30m",
        period="7d",
        engine=engine,
    )

    weather = station_observations_api(
        station_code="009021",
        interval="30m",
        period="7d",
        network_code="WEM",
        engine=engine,
    )

    price = price_network_region_api(
        engine=engine,
        network_code="WEM",
        network_region_code="WEM",
        interval="30m",
        period="7d",
    )

    # demand = wem_demand()

    stats.data = stats.data + price.data + weather.data

    return stats


@router.get(
    "/{network_code}/energy/daily/{year}.json",
    name="Network energy by year",
    response_model_exclude_unset=True,
    response_model=OpennemDataSet,
)
def api_export_energy_year(
    engine: Any = Depends(get_database_engine),
    network_code: str = Query("WEM", description="Network code"),
    year: int = Query(YEAR_CURRENT, description="Year to query"),
) -> OpennemDataSet:
    if year > YEAR_CURRENT or year < 1996:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid year"
        )

    network: NetworkSchema = network_from_network_code(network_code)

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid network",
        )

    stats = energy_network_fueltech_api(
        network_code=network.code,
        network_region=None,
        interval="1d",
        year=year,
        period="1Y",
        engine=engine,
    )

    weather = station_observations_api(
        station_code="009021",
        interval="1d",
        year=year,
        network_code="WEM",
        engine=engine,
        period=None,
    )

    price = price_network_region_api(
        engine=engine,
        network_code="WEM",
        network_region_code="WEM",
        interval="1d",
        period=None,
        year=year,
    )

    stats.data += weather.data + price.data

    return stats


@router.get(
    "/{network_code}/energy/monthly/{month}.json",
    name="Network energy by month",
    response_model_exclude_unset=True,
    response_model=OpennemDataSet,
)
def api_export_energy_month(
    engine: Any = Depends(get_database_engine),
    network_code: str = Query("WEM", description="Network code"),
    month: str = Query("all", description="Month to query"),
) -> OpennemDataSet:
    network: NetworkSchema = network_from_network_code(network_code)

    if month != "all":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Other months not yet supported",
        )

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid network",
        )

    stats = energy_network_fueltech_api(
        network_code=network.code,
        period="all",
        engine=engine,
        interval="1M",
        network_region=None,
    )

    price = price_network_region_api(
        engine=engine,
        network_code="WEM",
        network_region_code="WEM",
        interval="1M",
        period="all",
    )
    stats.data += price.data

    return stats
