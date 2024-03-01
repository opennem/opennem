"""Parse MMS filenames"""

import enum
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

from opennem.schema.network import NetworkSchema

logger = logging.getLogger("openne.core.parsers.aemo_filename")

__aemo_filename_re = re.compile(r"(?P<filename>[a-zA-Z\_]+)_(?P<date>\d{6,14})_?(?P<interval>\d{8,16})?\.(zip|csv)")


class AEMODataBucketSize(enum.Enum):
    interval = "interval"
    day = "day"
    week = "week"
    fortnight = "fortnight"
    month = "month"
    year = "year"


@dataclass
class AEMOMMSFilename:
    filename: str
    date: datetime | None = field(default=None)
    interval: str | None = field(default=None)
    bucket_size: AEMODataBucketSize | None = field(default=None)


def parse_aemo_filename_datetimes(dtimestr: str, network: NetworkSchema | None = None) -> datetime:
    """Takes a date string from AEMO nemweb filenames and returns a datetime"""

    dt: datetime | None = None

    AEMO_FORMATS = [
        "%Y%m%d",
        "%Y%m%d%H%M",
        "%Y%m%d%H%M%S",
    ]

    for _fmt in AEMO_FORMATS:
        try:
            dt = datetime.strptime(dtimestr, _fmt)

            if dt:
                break
        except ValueError:
            pass

    if not dt:
        raise Exception(f"Could not parse AEMO filename datetime {dtimestr}")

    if network and network.get_timezone():
        dt = dt.astimezone(network.get_timezone())  # type: ignore

    return dt


def parse_aemo_filename(filename: str) -> AEMOMMSFilename:
    """Takes an AEMO filename and parses it into it's components"""

    filename_components = re.search(__aemo_filename_re, filename.strip())

    if not filename_components:
        raise Exception(f"Could not parse filename {filename}")

    date_parsed = None

    try:
        date_parsed = parse_aemo_filename_datetimes(filename_components.group("date"))
    except Exception as e:
        logger.info("Could not parse filename datetimes {}: {}".format(filename_components.group("filename"), e))

    filename_model = AEMOMMSFilename(
        filename=filename_components.group("filename"),
        date=date_parsed,
        interval=filename_components.group("interval"),
    )

    return filename_model
