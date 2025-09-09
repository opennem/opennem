import logging
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta
from datetime import timezone as pytimezone
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from datedelta import datedelta
from dateutil.parser import ParserError, parse  # type: ignore
from dateutil.relativedelta import relativedelta

from opennem.core.networks import NetworkSchema
from opennem.core.normalizers import normalize_whitespace
from opennem.schema.network import NetworkNEM
from opennem.utils.timezone import is_aware, make_aware

# Sydney timezone for display
SYDNEY_TZ = ZoneInfo("Australia/Sydney")
BRISBANE_TZ = ZoneInfo("Australia/Brisbane")

logger = logging.getLogger(__name__)

# Date formats
# See: https://docs.python.org/3.8/library/datetime.html#strftime-and-strptime-behavior
DATE_FORMATS = [
    "%Y/%m/%d,%H:%M:%S",
    "%Y%m%d",
    #
    "%d/%m/%y %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%d/%m/%Y %I:%M:%S %p",  # excel format
    "%Y%m%d%H%M%S",  # bom format
]

DATE_CURRENT = datetime.now()

TODAY = datetime.now().date()

TODAY_NEM = datetime.now().astimezone(ZoneInfo("Australia/Brisbane"))

DATE_YESTERDAY = DATE_CURRENT - timedelta(days=1)

DATE_CURRENT_YEAR = DATE_CURRENT.year

CACHE_MAXSIZE = 12 * 1024


@lru_cache(maxsize=CACHE_MAXSIZE)
def optimized_data_parser(date_str: str) -> datetime | None:
    """
    Turns out that dateutil's date parser is slow since
    it does a lot of string parsing. Here we try matching
    the date using known string formats.
    """
    dt_return = None

    date_str = normalize_whitespace(date_str).strip()

    for date_format_str in DATE_FORMATS:
        try:
            dt_return = datetime.strptime(date_str, date_format_str)
        except (KeyError, OverflowError, ValueError, AttributeError):
            continue
        if dt_return:
            return dt_return

    return dt_return


@lru_cache(maxsize=CACHE_MAXSIZE)
def parse_date(
    date_str: str | datetime,
    date_format: str | None = None,
    network: NetworkSchema | None = None,
    dayfirst: bool = True,
    yearfirst: bool = False,
    is_utc: bool = False,
    timezone: pytimezone | None = None,
    use_optimized: bool = True,
) -> datetime | None:
    dt_return = None

    if isinstance(date_str, datetime):
        dt_return = date_str

    elif isinstance(date_str, str):
        # avoid strptime if we can
        try:
            dt_return = datetime.fromisoformat(date_str.replace("/", "-"))
        except ValueError:
            pass

        if not dt_return and date_format:
            dt_return = datetime.strptime(date_str, date_format)

        if not dt_return and use_optimized:
            dt_return = optimized_data_parser(date_str)

        if not dt_return:
            try:
                dt_return = parse(date_str, dayfirst=dayfirst, yearfirst=yearfirst)
            except ParserError:
                raise ValueError("Invalid date string passed") from None

    if network:
        tz = network.get_timezone()

        if tz:
            if is_aware(dt_return):
                if hasattr(tz, "localize"):
                    dt_return = tz.localize()  # type: ignore
                else:
                    dt_return = dt_return.replace(tzinfo=tz)  # type: ignore
            else:
                dt_return = make_aware(dt_return, timezone=tz)  # type: ignore

    if is_utc:
        tz = UTC

        if dt_return and is_aware(dt_return):
            if tz and hasattr(tz, "localize"):
                dt_return = tz.localize()  # type: ignore
            else:
                dt_return = dt_return.replace(tzinfo=tz)
        else:
            dt_return = make_aware(dt_return, timezone=tz)  # type: ignore

    if timezone:
        dt_return = make_aware(dt_return, timezone=timezone)  # type: ignore

    return dt_return


def date_series(
    start: datetime | date | None = None,
    end: datetime | date | None = None,
    length: int = 30,
    interval: timedelta | relativedelta = timedelta(days=1),
    reverse: bool = False,
) -> Generator[date, None, None]:
    """
    Generate a datetime series

    @NOTE probably don't need reverse since you can provide a negative interval

    """
    if start and isinstance(start, datetime):
        start = start.date()

    if end and isinstance(end, datetime):
        end = end.date()

    if not start:
        start = datetime.now().date()

    if end:
        # Calculating the number of intervals
        # is different between timedelta and
        # relative times
        if isinstance(interval, timedelta):
            length = int(abs((end - start) / interval))

        # currently only supports up to granuality months
        elif isinstance(interval, relativedelta):
            rd = relativedelta(start, end)

            length = rd.years * 12 + rd.months + 1

    next_record = start

    for _ in range(length):
        yield next_record

        if reverse:
            next_record -= interval
        else:
            next_record += interval


total_months = lambda dt: dt.month + 12 * dt.year  # noqa: E731


def total_weeks(d1: datetime | date, d2: datetime | date) -> int:
    monday1 = d1 - timedelta(days=d1.weekday())
    monday2 = d2 - timedelta(days=d2.weekday())

    return abs(int((monday2 - monday1).days / 7))  # type: ignore


def month_series(
    start: datetime | date,
    end: datetime | date,
    length: int | None = None,
    reverse: bool = False,
) -> Generator[datetime, None, None]:
    """
    Generate a series of months
    """
    step = 1

    if end < start:
        step = -1

    if start == end:
        yield datetime(start.year, start.month, 1)

    for tot_m in range(total_months(start) - 1, total_months(end) - 2, step):
        y, m = divmod(tot_m, 12)
        yield datetime(y, m + 1, 1)


def day_series(date_start: datetime, date_end: datetime) -> Generator[datetime, None, None]:
    """Generate a series of (midnight) days for a date range"""
    for n in range(int((date_end - date_start).days) + 1):
        yield date_start + timedelta(n)


def week_series(
    start: datetime | date,
    end: datetime | date,
    length: int | None = None,
) -> Generator[tuple[int, int], None, None]:
    """
    Generate week series M -> S
    """
    reverse = False

    if end < start:
        reverse = True

    length = total_weeks(start, end)

    for week_i in range(0, length):
        if reverse:
            cur_date = start - timedelta(weeks=week_i)
        else:
            cur_date = start + timedelta(weeks=week_i)

        cur_cal = cur_date.isocalendar()

        yield cur_cal[0], cur_cal[1]


def week_series_datetimes(
    start: datetime,
    end: datetime,
    length: int | None = None,
) -> Generator[tuple[datetime, datetime], None, None]:
    """
    Generate week series M -> S
    """
    reverse = False

    if end < start:
        reverse = True

    if not length:
        length = total_weeks(start, end)

    for week_i in range(0, length):
        if reverse:
            cur_date = start.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(weeks=week_i)
        else:
            cur_date = start.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(weeks=week_i)

        yield get_week_range_from_datetime(cur_date)


def get_week_start_from_week_num(year: int, week_no: int) -> datetime:
    """Get the week start from a week number"""
    return datetime.strptime(f"{year}-W{int(week_no)}-1", "%Y-W%W-%w")


def format_sydney_time(dt: datetime | None) -> str:
    """Format datetime in Sydney timezone in human readable format"""
    if not dt:
        return "Unknown"
    sydney_time = dt.astimezone(SYDNEY_TZ)
    return sydney_time.strftime("%d %b %I:%M%p").replace(" 0", " ").replace("AM", "am").replace("PM", "pm")


def get_week_range_from_datetime(subject: datetime) -> tuple[datetime, datetime]:
    """Get the datetime range of a week from a datetime"""
    start = subject - timedelta(days=subject.weekday())
    end = start + timedelta(days=6)
    return (start, end)


def get_week_number_from_datetime(subject: datetime) -> int:
    """Get the week number from a datetime"""
    return subject.isocalendar().week + 1


def get_current_week_for_network(network: NetworkSchema) -> int:
    """Gets the current week for a network"""
    return datetime.now().astimezone(network.get_fixed_offset()).date().isocalendar().week


def chop_delta_microseconds(delta: timedelta) -> timedelta:
    """Removes microsevonds from a timedelta"""
    return delta - timedelta(microseconds=delta.microseconds)


def chop_datetime_microseconds(dt: datetime) -> datetime:
    """Removes the microseconds portion of a datetime"""

    if not dt.microsecond:
        return dt

    return dt - timedelta(microseconds=dt.microsecond)


def chop_timezone(dt: datetime) -> datetime:
    """Removes the timezone of a datetime"""

    if not dt.tzinfo:
        return dt

    return dt.replace(tzinfo=None)


def get_date_component(format_str: str, dt: datetime | None = None, tz: Any | None = None) -> str:
    """
    Get the format string part out of a date

    ex.
    >>> get_date_component("%Y")
    > 2020
    """
    if not dt:
        dt = DATE_CURRENT

    if tz:
        try:
            dt = dt.astimezone(tz)
        except Exception:
            raise Exception(f"Invalid timezone: {tz}") from None

    date_str_component = dt.strftime(format_str)

    return date_str_component


def num_intervals_between_datetimes(interval: timedelta | datedelta, start_date: datetime, end_date: datetime) -> int:
    """
    Returns the number of intervals between two datetimes. If the interval is a day or larger it is inclusive.
    """

    if isinstance(interval, timedelta):
        intervals = int((end_date - start_date) / interval) + 1
    elif isinstance(interval, datedelta):
        intervals = 1
        while True:
            start_date += interval
            if start_date > end_date:
                break
            intervals += 1

    return intervals


def get_end_of_last_month(dt: datetime) -> datetime:
    """Get the end of the previous month"""
    dtn = dt.replace(day=1) - timedelta(days=1)

    return dtn


def get_last_complete_day_for_network(network: NetworkSchema) -> datetime:
    # today_midnight in network time
    today_midnight = datetime.now(network.get_fixed_offset()).replace(tzinfo=None, microsecond=0, hour=0, minute=0, second=0)

    return today_midnight


def get_last_completed_interval_for_network(network: NetworkSchema = NetworkNEM, tz_aware: bool = False) -> datetime:
    """Get the last completed network time for a network. Live wall clock"""
    now_network = datetime.now(network.get_fixed_offset())

    if not tz_aware:
        now_network = now_network.replace(tzinfo=None)

    return now_network.replace(
        minute=now_network.minute - (now_network.minute % network.interval_size),
        second=0,
        microsecond=0,
    )


def get_today_nem() -> datetime:
    """Gets today in NEM time"""
    now = datetime.now()

    now_no_microseconds = now.replace(microsecond=0)

    # NEM is fixed offset at +10
    nem_tz = NetworkNEM.get_fixed_offset()

    nem_dt = now_no_microseconds.astimezone(nem_tz)

    return nem_dt


def get_today_for_network(network: NetworkSchema) -> datetime:
    """Gets today in NEM time"""
    now = datetime.now()

    now_no_microseconds = now.replace(microsecond=0)

    # NEM is fixed offset at +10
    nem_tz = network.get_fixed_offset()

    nem_dt = now_no_microseconds.astimezone(nem_tz)

    return nem_dt


def get_today_opennem() -> datetime:
    """OpenNEM time is Sydney / Melbourne"""
    return datetime.now(ZoneInfo("Australia/Sydney")).replace(microsecond=0)
