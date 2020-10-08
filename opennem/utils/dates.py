import logging
from datetime import datetime, timezone
from typing import Optional, Union

from dateutil.parser import ParserError, parse

from opennem.core.networks import NetworkSchema
from opennem.utils.timezone import UTC, is_aware, make_aware

logger = logging.getLogger(__name__)


def parse_date(
    date_str: Union[str, datetime],
    network: Optional[NetworkSchema] = None,
    dayfirst: bool = True,
    yearfirst: bool = False,
    is_utc: bool = False,
    timezone: timezone = False,
) -> Optional[datetime]:
    dt_return = None

    if isinstance(date_str, datetime):
        dt_return = date_str

    elif isinstance(date_str, str):
        try:
            dt_return = parse(date_str, dayfirst=dayfirst, yearfirst=yearfirst)
        except ParserError:
            raise ValueError("Invalid date string passed")

    else:
        raise ValueError("Require a datetime or string object to parse date")

    if network:
        tz = network.get_timezone()

        if tz:
            dt_return = make_aware(dt_return, timezone=tz)

    if is_utc:
        dt_return = make_aware(dt_return, timezone=UTC)

    if timezone:
        dt_return = make_aware(dt_return, timezone=timezone)

    return dt_return
