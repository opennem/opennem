from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from opennem.core.networks import NetworkNEM, NetworkWEM
from opennem.db import get_database_engine

from .schema import ScraperStats, ScraperStatsResult

router = APIRouter()


@router.get("/scraper/stats", response_model=List[ScraperStatsResult])
def scraper_stats(
    engine=Depends(get_database_engine),
) -> List[ScraperStatsResult]:
    query = """
        select
            count(fs.trading_interval),
            max(fs.trading_interval),
            min(fs.trading_interval)
        from facility_scada fs where fs.network_id='WEM'
        union select
            count(fs.trading_interval),
            max(fs.trading_interval),
            min(fs.trading_interval)
        from facility_scada fs where fs.network_id='NEM'
    """

    results = []

    with engine.connect() as c:
        results = list(c.execute(query))

    if not len(results):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not implemented"
        )

    result = []

    result.append(
        ScraperStatsResult(
            network=NetworkWEM,
            stats=ScraperStats(
                scada_intervals=results[0][0],
                scada_max=results[0][1],
                scada_min=results[0][2],
            ),
        )
    )

    result.append(
        ScraperStatsResult(
            network=NetworkNEM,
            stats=ScraperStats(
                scada_intervals=results[1][0],
                scada_max=results[1][1],
                scada_min=results[1][2],
            ),
        )
    )

    return result
