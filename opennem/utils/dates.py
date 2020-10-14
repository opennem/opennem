import logging
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Union

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
            if is_aware(dt_return):
                if hasattr(tz, "localize"):
                    dt_return = tz.localize()
                else:
                    dt_return = dt_return.replace(tzinfo=tz)
            else:
                dt_return = make_aware(dt_return, timezone=tz)

    if is_utc:
        tz = UTC

        if is_aware(dt_return):
            if hasattr(tz, "localize"):
                dt_return = tz.localize()
            else:
                dt_return = dt_return.replace(tzinfo=tz)
        else:
            dt_return = make_aware(dt_return, timezone=tz)

    if timezone:
        dt_return = make_aware(dt_return, timezone=timezone)

    return dt_return


def get_date_component(format_str: str) -> str:
    """
        Get a part of a date
    """

    return datetime.now().strftime(format_str)


def date_series(
    start: Union[datetime, date] = None,
    end: Union[datetime, date] = None,
    length: int = 30,
    interval: timedelta = timedelta(days=1),
    reverse: bool = False,
) -> List[datetime]:
    """
        Generate a datetime series

    """
    if start and isinstance(start, datetime):
        start = start.date()

    if end and isinstance(end, datetime):
        end = start.date()

    if not start:
        start = datetime.now().date()

    if end:
        length = int(abs((end - start) / interval))

    next_record = start

    for _ in range(length):
        if reverse:
            next_record -= interval
        else:
            next_record += interval

        yield next_record
