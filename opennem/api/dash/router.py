""" Dashboard API Router

Interval for OpenNEM frontends
"""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.engine.base import Engine
from starlette import status

from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_period
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.queries.price import get_network_region_price_query
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.api.now")

router = APIRouter()


@router.get(
    "/now",
    name="Live Dashboard view results",
    response_model=OpennemDataSet,
    response_model_exclude_unset=True,
    include_in_schema=False,
)
# @cache(expire=60 * 5)
async def now_endpoint(
    engine: Engine = Depends(get_database_engine),
) -> OpennemDataSet:
    """
    Args:
        engine ([type], optional): Database engine. Defaults to Depends(get_database_engine).

    Raises:
        HTTPException: No results

    Returns:
        OpennemData: data set
    """
    engine = get_database_engine()
    human_to_period("1d")
    network = NetworkNEM

    last_completed_interval = get_last_completed_interval_for_network(network=network)

    if not network.get_interval():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network has no interval",
        )

    # price
    query = get_network_region_price_query(
        date_min=last_completed_interval - timedelta(days=1),
        date_max=last_completed_interval,
        interval=network.get_interval(),
        network=network,
    )

    with engine.begin() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    result_set = [DataQueryResult(interval=i[0], result=i[3], group_by=i[2] if len(i) > 1 else None) for i in row]

    response_model = stats_factory(
        result_set,
        network=network,
        interval=network.get_interval(),
        units=get_unit("price"),
        group_field="price",
        include_group_code=True,
        include_code=True,
    )

    if not response_model or not response_model.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results",
        )

    return response_model

    # flows
    # query = interconnector_flow_network_regions_query(time_series=time_series, network_region=network_region_code)

    # with engine.connect() as c:
    #     logger.debug(query)
    #     row = list(c.execute(query))

    # if not row:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No results")

    # imports = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]

    # result = stats_factory(
    #     imports,
    #     # code=network_region_code or network.code,
    #     network=time_series.network,
    #     interval=time_series.interval,
    #     units=get_unit("regional_trade"),
    #     # fueltech_group=True,
    #     group_field="power",
    #     include_group_code=True,
    #     include_code=True,
    # )
    # return result
