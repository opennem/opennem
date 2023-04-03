import logging

from opennem.db import get_database_engine
from opennem.db.views import get_timescale_view_names
from opennem.utils.dates import subtract_days

logger = logging.getLogger("opennem.db.tasks")


def refresh_timescale_views(view_name: str | None = None, all: bool = False, days: int = 7) -> None:
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
    date_from = f"""'{dt.strftime("%Y-%m-%d")}'"""

    if all:
        date_from = "NULL"

    views = []

    if view_name:
        views.append(view_name)
    else:
        views = get_timescale_view_names()

    with engine.connect() as c:
        for v in views:
            query = __query.format(view=v, date_from=date_from)
            logger.debug(query)

            try:
                c.execution_options(isolation_level="AUTOCOMMIT").execute(query)
            except Exception as e:
                logger.error(f"Could not run refresh: {e}")


def refresh_views() -> None:
    refresh_timescale_views(all=True)


if __name__ == "__main__":
    refresh_views()
