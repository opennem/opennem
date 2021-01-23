import logging
from typing import Optional

from opennem.db import get_database_engine
from opennem.utils.dates import subtract_days

logger = logging.getLogger("opennem.db.tasks")

TIMESCALE_VIEWS = [
    "mv_facility_energy_hour",
    "mv_nem_facility_power_5min",
    "mv_interchange_energy_nem_region",
    "mv_interchange_power_nem_region",
    "mv_wem_facility_power_30min",
]

MATERIAL_VIEWS = ["mv_facility_all", "mv_region_emissions"]


def refresh_timescale_views(
    view_name: Optional[str] = None, all: bool = False, days: int = 7
) -> None:
    """refresh timescale views"""
    __query = """
    CALL refresh_continuous_aggregate(
        continuous_aggregate => '{view}',
        window_start         => {date_from},
        window_end           => NULL
    );
    """

    engine = get_database_engine()
    dt = subtract_days(days=days)
    date_from = "'{}'".format(dt.strftime("%Y-%m-%d"))

    if all:
        date_from = "NULL"

    views = []

    if view_name:
        views.append(view_name)
    else:
        views = TIMESCALE_VIEWS

    with engine.connect() as c:
        for v in TIMESCALE_VIEWS:
            query = __query.format(view=v, date_from=date_from)
            logger.debug(query)
            c.execution_options(isolation_level="AUTOCOMMIT").execute(query)


def refresh_material_views(view_name: Optional[str] = None) -> None:
    """Refresh material views"""
    __query = "REFRESH MATERIALIZED VIEW CONCURRENTLY {view} with data"

    engine = get_database_engine()

    views = []

    if view_name:
        views.append(view_name)
    else:
        views = MATERIAL_VIEWS

    with engine.connect() as c:
        for v in views:
            query = __query.format(view=v)
            logger.debug(query)
            c.execution_options(isolation_level="AUTOCOMMIT").execute(query)


def refresh_views() -> None:
    refresh_timescale_views(all=True)
    refresh_material_views()


if __name__ == "__main__":
    refresh_views()
