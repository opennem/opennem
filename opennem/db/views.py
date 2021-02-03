import logging

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.db.views")


def init_views() -> None:
    logger.info("init views")


if __name__ == "__main__":
    init_views()
