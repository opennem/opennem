from opennem.db import get_database_engine

VIEWS = ["mv_facility_energy_hour", "mv_facility_all"]


def refresh_views() -> None:
    """Refresh material views"""
    __query = "REFRESH MATERIALIZED VIEW CONCURRENTLY {view} with data"

    engine = get_database_engine()

    with engine.connect() as c:
        for v in VIEWS:
            query = __query.format(view=v)
            c.execution_options(isolation_level="AUTOCOMMIT").execute(query)


if __name__ == "__main__":
    refresh_views()
