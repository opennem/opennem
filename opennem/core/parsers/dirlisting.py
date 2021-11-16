"""OpenNEM Directory Listing Parser

Used to parse default http server directory listings and returns a list of file
objects

Currently supports:

    * IIS default listings and variations

"""

import html
import logging
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from pydantic import ValidationError, validator
from scrapy.http import HtmlResponse

from opennem.core.normalizers import strip_double_spaces
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.parsers.dirlisting")

__iis_line_match = re.compile(
    r"(?P<modified_date>.*[AM|PM])\ {2,}(?P<file_size>(\d{1,}|\<dir\>))\ <a href=['\"]?(?P<link>[^'\" >]+)['\"]>(?P<filename>[^\<]+)"
)


def parse_dirlisting_datetime(datetime_string: Union[str, datetime]) -> Optional[datetime]:
    """Parses dates from directory listings. Primarily used for modified time"""

    # sometimes it already parses via pydantic
    if isinstance(datetime_string, datetime):
        return datetime_string

    datetime_string = strip_double_spaces(datetime_string.strip())

    if not datetime_string:
        logger.error("No dirlisting datetime string")

    _FORMAT_STRINGS = ["%A, %B %d, %Y %I:%M %p"]

    datetime_parsed: Optional[datetime] = None

    for _fs in _FORMAT_STRINGS:
        try:
            datetime_parsed = datetime.strptime(datetime_string, _fs)
        except ValueError:
            pass

    if not datetime_string:
        logger.error("Error parsing dirlisting datetime string: {}".format(datetime_string))

    return datetime_parsed


class DirlistingEntryType(Enum):
    file = "file"
    directory = "directory"


class DirlistingEntry(BaseConfig):
    filename: Path
    link: str
    modified_date: Optional[datetime]
    file_size: Optional[int]
    entry_type: DirlistingEntryType = DirlistingEntryType.file

    _validate_modified_date = validator("modified_date", allow_reuse=True, pre=True)(
        parse_dirlisting_datetime
    )

    @validator("file_size", allow_reuse=True, pre=True)
    def _parse_dirlisting_filesize(cls, value: str):
        if value != "<dir>":
            return value

        return None


def parse_dirlisting_line(dirlisting_line: str) -> Optional[DirlistingEntry]:
    """Parses a single line from a dirlisting page"""

    matches = re.search(__iis_line_match, dirlisting_line)

    model: Optional[DirlistingEntry] = None

    if not matches:
        logger.error("Could not match dirlisting line: {}".format(dirlisting_line))
        return None

    try:
        model = DirlistingEntry(**matches.groupdict())
    except ValidationError as e:
        logger.error("Error in validating dirlisting line: {}".format(e))
    except ValueError as e:
        logger.error("Error parsing dirlisting line: {}".format(e))

    return model


def parse_dirlisting(dirlisting_content: str) -> List[DirlistingEntry]:
    resp = HtmlResponse(url="http://none", body=dirlisting_content, encoding="utf-8")

    _dirlisting_models: List[DirlistingEntry] = []

    for i in resp.css("body pre").get().split("<br>"):
        if "pre>" in i:
            continue

        model = parse_dirlisting_line(html.unescape(i.strip()))

        if model:
            if not model.file_size or model.link.endswith("/"):
                model.entry_type = DirlistingEntryType.directory

            _dirlisting_models.append(model)

    return _dirlisting_models
