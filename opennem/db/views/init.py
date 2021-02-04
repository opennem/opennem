import logging

from opennem.db.views import init_aggregation_policies, init_database_views, purge_views

logger = logging.getLogger("opennem.db.views")


def init_views_cli(purge: bool = False) -> None:
    logger.info("init views")

    if purge:
        purge_views()

    init_database_views()
    init_aggregation_policies()


if __name__ == "__main__":
    purge_views()
    init_database_views()
    init_aggregation_policies()
