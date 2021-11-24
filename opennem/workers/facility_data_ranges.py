"""
For each facility calculate the first and last data seen dates from facility_scada

The min dates are run less regularly since data is less likely to grow in that direction
for most recent this is the last active date

@TODO move the utility functions into core/facility use this as only the worker
"""
import logging
from datetime import datetime
from textwrap import dedent
from typing import List, Optional

from opennem.db import get_database_engine
from opennem.notifications.slack import slack_message
from opennem.schema.core import BaseConfig
from opennem.utils.sql import duid_in_case

logger = logging.getLogger("opennem.workers.facility_data_ranges")


def get_update_seen_query(
    include_first_seen: bool = True,
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
        where fs.generated > 0 or fs.eoi_quantity is not null
        {facility_codes_query}
        group by 1
    ) as seen_query
    where f.code = seen_query.code;
    """

    fs = "" if include_first_seen else "--"
    facility_codes_query = (
        f"and f.code in ({duid_in_case(facility_codes)})" if facility_codes else ""
    )

    query = __query.format(fs=fs, facility_codes_query=facility_codes_query)

    return dedent(query)


def update_facility_seen_range(
    include_first_seen: bool = False,
    facility_codes: Optional[List[str]] = None,
) -> bool:
    """Updates last seen and first seen. For each facility updates the date the facility
    was seen for the first and last time in the power data from FacilityScada.

    Args:
        include_first_seen (bool, optional): Include earliest seen time. Defaults to False.
        facility_codes (Optional[List[str]], optional): List of facility codes to update. Defaults to None.

    Returns:
        bool: Ran successfuly
    """

    engine = get_database_engine()

    __query = get_update_seen_query(
        include_first_seen=include_first_seen, facility_codes=facility_codes
    )

    with engine.connect() as c:
        logger.debug(__query)
        c.execute(__query)

    return True


class FacilitySeenRange(BaseConfig):
    date_min: Optional[datetime]
    date_max: Optional[datetime]


def get_facility_seen_range(facility_codes: List[str]) -> FacilitySeenRange:
    """Gets the date range that a facility or list of facilities was seen in SCADA data.


    Args:
        facility_codes (Optional[List[str]], optional): List of facility codes to update. Defaults to None.

    Returns:
        FacilitySeenRange: Schema defining the date range
    """

    __query = """
        select
            min(data_first_seen) as first_seen,
            max(data_last_seen) as last_seen
        from facility
        where code in ({facilities});
    """

    engine = get_database_engine()
    result = []

    query = __query.format(facilities=duid_in_case(facility_codes))

    with engine.connect() as c:
        logger.debug(query)
        result = list(c.execute(query))

    if not result:
        raise Exception("Could not get facility seen range: No results")

    _record = result.pop()

    if len(_record) != 2:
        raise Exception("Coult not get facility seen range: Invalid result or unknown")

    schema = FacilitySeenRange(
        date_min=_record[0],
        date_max=_record[1],
    )

    return schema


if __name__ == "__main__":
    update_facility_seen_range(True)
