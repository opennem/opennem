from opennem.db import get_database_engine


def refresh_views() -> None:
    """Refresh material views"""
    __query = "REFRESH MATERIALIZED VIEW CONCURRENTLY {view} with data"

    engine = get_database_engine()

    with engine.connect() as c:
        c.execute(__query)


if __name__ == "__main__":
    refresh_views()
