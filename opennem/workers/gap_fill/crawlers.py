"""" Utility to gap fill crawlers """
import logging

from sqlalchemy.sql import text

from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig


def query_crawler_gaps() -> None:
    """Query crawler gaps"""
    engine = get_database_engine()

    query = text(
        """
        select
            time_bucket_gapfill('5 min')

        from crawl_history ch

    """
    )


logger = logging.getLogger("openne.gap_fill.crawlers")
