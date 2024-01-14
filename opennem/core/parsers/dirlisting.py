# pylint: disable=no-self-argument
"""OpenNEM Directory Listing Parser

Used to parse default http server directory listings and returns a list of file
objects

Currently supports:

    * IIS default listings and variations
    * Extracing metadata from AEMO filenames
"""

import html
import logging
import re
from datetime import datetime
from enum import Enum
from operator import attrgetter
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from pydantic import ValidationError, validator
from pyquery import PyQuery as pq

from opennem.core.downloader import url_downloader
from opennem.core.normalizers import is_number, strip_double_spaces
from opennem.core.parsers.aemo.filenames import parse_aemo_filename
from opennem.schema.core import BaseConfig
from opennem.schema.date_range import CrawlDateRange

logger = logging.getLogger("opennem.parsers.dirlisting")

__iis_line_match = re.compile(
    r"(?P<modified_date>.*[AM|PM])\ {2,}(?P<file_size>(\d{1,}|\<dir\>))\ "
    r"<a href=['\"]?(?P<link>[^'\" >]+)['\"]>(?P<filename>[^\<]+)"
)

__nemweb_line_match = re.compile(
    r"(?P<modified_date>\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} [AP]M)\s{2,}(?P<file_size>\d+)\s+"
    r"<a href=\"(?P<link>[^\"]+)\">(?P<filename>[^<]+)"
)

__nemweb_line_match_2 = re.compile(
    r"(?P<modified_date>\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)\s+(?P<file_size>\d+)"
    r"\s+<a href=\"(?P<link>[^\"]+)\">(?P<filename>[^<]+)"
)

# AEMO files have a created timestamp in their filenames. This extracts it.
_aemo_created_date_match = re.compile(r"\_(?P<date_created>\d{12})\_")


def parse_dirlisting_datetime(datetime_string: str | datetime) -> datetime | None:
    """Parses dates from directory listings. Primarily used for modified time"""

    # sometimes it already parses via pydantic
    if isinstance(datetime_string, datetime):
        return datetime_string

    datetime_string = strip_double_spaces(datetime_string.strip())

    if not datetime_string:
        logger.error("No dirlisting datetime string")

    # Wednesday, December 28, 2022 9:10
    _FORMAT_STRINGS = ["%A, %B %d, %Y %I:%M %p", "%A, %B %d, %Y %I:%M", "%m/%d/%Y %I:%M %p", ""]

    datetime_parsed: datetime | None = None

    for _fs in _FORMAT_STRINGS:
        try:
            datetime_parsed = datetime.strptime(datetime_string, _fs)
        except ValueError:
            pass

    if not datetime_string:
        logger.error(f"Error parsing dirlisting datetime string: {datetime_string}")

    return datetime_parsed


class DirlistingEntryType(Enum):
    file = "file"
    directory = "directory"


class DirlistingEntry(BaseConfig):
    filename: Path
    link: str
    modified_date: datetime
    aemo_interval_date: datetime | None
    file_size: int | None
    entry_type: DirlistingEntryType = DirlistingEntryType.file

    _validate_modified_date = validator("modified_date", allow_reuse=True, pre=True)(parse_dirlisting_datetime)

    @validator("aemo_interval_date", always=True)
    def _validate_aemo_created_date(cls, value: Any, values: dict[str, Any]) -> datetime | None:
        if value:
            raise Exception("aemGo_interval_date is derived, not set")

        # no need to check if this exists since ValidationError will occur if not
        _filename_value: Path = values["filename"]
        aemo_dt = None

        if _filename_value.suffix.lower() not in [".zip", ".csv"]:
            return None

        try:
            aemo_dt = parse_aemo_filename(str(_filename_value))
        except Exception as e:
            logger.info(f"Error parsing aemo datetime: {e}")
            return None

        return aemo_dt.date

    @validator("file_size", allow_reuse=True, pre=True)
    def _parse_dirlisting_filesize(cls, value: str | int | float) -> str | int | float | None:
        if is_number(value):
            return value

        return None

    @validator("entry_type", always=True)
    def _validate_entry_type(cls, value: Any, values: dict[str, Any]) -> DirlistingEntryType:
        if not values["file_size"]:
            return DirlistingEntryType.directory

        if values["link"].endswith("/"):
            return DirlistingEntryType.directory

        return DirlistingEntryType.file


class DirectoryListing(BaseConfig):
    url: str
    timezone: str | None
    entries: list[DirlistingEntry] = []

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def file_count(self) -> int:
        return len(self.get_files())

    @property
    def directory_count(self) -> int:
        return len(self.get_directories())

    def apply_date_range(self, date_range: CrawlDateRange) -> None:
        self.entries = list(
            filter(
                lambda x: x.modified_date and x.modified_date > date_range.start and x.modified_date < date_range.end,
                self.entries,
            )
        )

    def apply_filter(self, pattern: str) -> None:
        self.entries = list(filter(lambda x: re.match(pattern, x.link), self.entries))

    def get_files(self) -> list[DirlistingEntry]:
        return list(filter(lambda x: x.entry_type == DirlistingEntryType.file, self.entries))

    def get_directories(self) -> list[DirlistingEntry]:
        return list(filter(lambda x: x.entry_type == DirlistingEntryType.directory, self.entries))

    def get_most_recent_files(self, reverse: bool = True, limit: int | None = None) -> list[DirlistingEntry]:
        obtained_files = self.get_files()

        if not obtained_files:
            return []

        _entries = sorted(obtained_files, key=attrgetter("modified_date"), reverse=reverse)

        if not limit:
            self.entries = _entries
            return _entries

        self.entries = _entries[:limit]

        return self.entries

    def get_files_modified_in(self, intervals: list[datetime]) -> list[DirlistingEntry]:
        return list(filter(lambda x: x.modified_date in intervals, self.entries))

    def get_files_aemo_intervals(self, intervals: list[datetime]) -> list[DirlistingEntry]:
        return list(filter(lambda x: x.aemo_interval_date in intervals, self.entries))

    def get_files_modified_since(self, modified_date: datetime) -> list[DirlistingEntry]:
        modified_since: list[DirlistingEntry] = []

        if self.timezone:
            # sanity check the timezone before filter
            try:
                ZoneInfo(self.timezone)
            except ValueError:
                raise Exception(f"Invalid dirlisting timezone: {self.timezone}") from None

            modified_since = list(
                filter(
                    lambda x: x.modified_date > modified_date,
                    self.get_files(),
                )
            )
        else:
            modified_since = list(filter(lambda x: x.modified_date > modified_date, self.get_files()))

        return modified_since


def parse_dirlisting_line(dirlisting_line: str) -> DirlistingEntry | None:
    """Parses a single line from a dirlisting page"""
    if not dirlisting_line:
        return None

    for _match in [__iis_line_match, __nemweb_line_match_2]:
        matches = _match.search(dirlisting_line)

        if not matches:
            continue

        not_empty = len([i for i in matches.groupdict() if i]) == 4

        if not_empty:
            break

    model: DirlistingEntry | None = None

    if not matches:
        logger.error(f"Could not match dirlisting line: {dirlisting_line}")
        return None

    try:
        model = DirlistingEntry(**matches.groupdict())
    except ValidationError as e:
        logger.error(f"Error in validating dirlisting line: {e}")
    except ValueError as e:
        logger.error(f"Error parsing dirlisting line: {e}")

    return model


def get_dirlisting(url: str, timezone: str | None = None) -> DirectoryListing:
    """Parse a directory listng into a list of DirlistingEntry models"""
    dirlisting_content = url_downloader(url)

    resp = pq(dirlisting_content.decode("utf-8"))

    _dirlisting_models: list[DirlistingEntry] = []

    pre_area = resp("pre")

    if not pre_area:
        raise Exception("Invalid directory listing: no pre or bad html")

    for i in [i for i in pre_area.html().split("<br/>") if i]:
        # it catches the containing block so skip those
        if not i:
            continue

        if "pre>" in i:
            continue

        if "To Parent Directory" in i:
            continue

        dirlisting_line = html.unescape(i.strip())

        model = parse_dirlisting_line(dirlisting_line)

        if model:
            # append the base URL to the model link
            model.link = urljoin(url, model.link)

            _dirlisting_models.append(model)

    listing_model = DirectoryListing(url=url, timezone=timezone, entries=_dirlisting_models)

    logger.debug(f"Got back {len(listing_model.entries)} models")

    return listing_model


# debug entry point
if __name__ == "__main__":
    url = "https://data.wa.aemo.com.au/public/market-data/wemde/tradingReport/tradingDayReport/previous/"

    dirlisting = get_dirlisting(url, timezone="Australia/Perth")

    print(dirlisting.entries[0])
