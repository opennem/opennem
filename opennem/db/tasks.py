from opennem.db import get_database_engine


def refresh_views() -> None:
    """Refresh material views"""
    __query = "REFRESH MATERIALIZED VIEW mv_facility_all with data"

    engine = get_database_engine()

    with engine.connect() as c:
        c.execute(__query)
