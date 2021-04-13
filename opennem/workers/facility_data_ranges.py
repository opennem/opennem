"""
For each facility calculate the first and last data seen dates from facility_scada

The min dates are run less regularly since data is less likely to grow in that direction
for most recent this is the last active date
"""
import logging
from textwrap import dedent
from typing import List, Optional

from opennem.api.stats.controllers import duid_in_case
from opennem.db import get_database_engine
from opennem.notifications.slack import slack_message

logger = logging.getLogger("opennem.workers.facility_data_ranges")


def get_update_seen_query(
    last_seen: bool = True,
    facility_codes: Optional[List[str]] = None,
) -> str:
    __query = """
    update facility f set
        {fs}data_first_seen = seen_query.data_first_seen,
        data_last_seen = seen_query.data_last_seen
    from (
        select
            f.code as code,
            {fs}min(fs.trading_interval) as data_first_seen,
            max(fs.trading_interval) as data_last_seen
            from facility_scada fs
        left join facility f on fs.facility_code = f.code
        where fs.generated > 0
        {facility_codes_query}
        group by 1
    ) as seen_query
    where f.code = seen_query.code;
    """

    fs = ""
    facility_codes_query = ""

    if not last_seen:
        fs = "--"

    if facility_codes:
        facility_codes_query = f"and f.code in ({duid_in_case(facility_codes)})"

    query = __query.format(fs=fs, facility_codes_query=facility_codes_query)

    return dedent(query)


def update_facility_seen_range(
    last_seen: bool = True,
    facility_codes: Optional[List[str]] = None,
) -> bool:
    """Updates last seen and first seen"""

    engine = get_database_engine()

    __query = get_update_seen_query(last_seen, facility_codes)

    with engine.connect() as c:
        logger.debug(__query)
        c.execute(__query)

    slack_message("Ran facility_seen_range")

    return True


if __name__ == "__main__":
    update_facility_seen_range(False)
