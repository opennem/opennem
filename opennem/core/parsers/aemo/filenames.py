""" Parse MMS filenames """

import re
from dataclasses import dataclass
from datetime import datetime

from opennem.schema.network import NetworkNEM, NetworkSchema

__aemo_filename_re = re.compile(r"(?P<filename>[\w\_]+)_(?P<date>\d{8,14})_(?P<interval>\d{16})\.zip")


@dataclass
class AEMOMMSFilename:
    filename: str
    date: int
    interval: str


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

    filename_model = AEMOMMSFilename(**filename_components.groupdict())

    return filename_model
