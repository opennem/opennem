#!/usr/bin/env python
"""
OpenNEM BoM Observation Archive Crawler

"""
import logging
import re
from enum import Enum
from io import BytesIO
from typing import Any, Dict
from urllib.parse import urlencode, urljoin
from zipfile import ZipFile

from opennem.utils.handlers import _handle_zip, chain_streams, open
from opennem.utils.http import http
from opennem.utils.mime import mime_from_content

logger = logging.getLogger("opennem.bom.archive")

logging.getLogger().setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)


class ObservationTypes(Enum):
    rain = 136
    temp_min = 123
    temp_max = 122
    solar = 193


BOM_BASE_URL = "http://www.bom.gov.au/jsp/ncc/cdio/weatherData/av"

BOM_DIRECTORY_PARAMS = {
    "p_stn_num": None,
    "p_display_type": "availableYears",
    "p_nccObsCode": ObservationTypes.temp_max.value,
}

BOM_RESOURCE_PARAMS = {
    "p_display_type": "dailyZippedDataFile",
    # station code
    "p_stn_num": None,
    # pcode
    "p_c": None,
    "p_nccObsCode": ObservationTypes.temp_max.value,
}

_directory_match = re.compile(r"^(?P<year>\d{4})\:(?P<id>\-\d+)$")


def _parse_directory(directory_response: bytes) -> Dict[int, str]:
    dir_components = directory_response.decode("utf-8").split(",")[1:]

    return_components = dict()

    for dir_comp in dir_components:
        dir_comp_m = re.match(_directory_match, dir_comp)

        if not dir_comp_m:
            continue

        return_components[int(dir_comp_m.group("year"))] = dir_comp_m.group("id")

    return return_components


def _unzip_content(content: Any) -> bytes:
    content = BytesIO(content)

    file_mime = mime_from_content(content)

    # @TODO handle all this in utils/archive.py
    # and make it all generic to handle other
    # mime types
    if file_mime == "application/zip":
        with ZipFile(content) as zf:
            if len(zf.namelist()) == 1:
                return zf.open(zf.namelist()[0]).read()

            c = []
            stream_count = 0

            for filename in zf.namelist():
                if filename.endswith(".zip"):
                    c.append(_handle_zip(zf.open(filename), "r"))
                    stream_count += 1
                else:
                    c.append(zf.open(filename))

            return chain_streams(c).read()

    return content.getvalue()


def bom_get_historic(station_code: str, year: int = 2021) -> None:

    params = BOM_DIRECTORY_PARAMS.copy()
    params["p_stn_num"] = station_code

    url = urljoin(BOM_BASE_URL, urlencode(params))

    r = http.get(BOM_BASE_URL, params=urlencode(params))

    if not r.ok:
        logger.error("Could not fetch url: {}".format(url))

    dc = _parse_directory(r.content)

    # Get observation

    if year not in dc.keys():
        raise Exception("Could not find year {} for station {}".format(year, station_code))

    directory_code = dc[year]

    params = BOM_RESOURCE_PARAMS.copy()
    params["p_stn_num"] = station_code
    params["p_c"] = directory_code

    r = http.get(BOM_BASE_URL, params=urlencode(params))

    if not r.ok:
        raise Exception("Url error in getting observation file")

    print(_unzip_content(r.content).decode("utf-8"))

    return None


if __name__ == "__main__":
    bom_get_historic("66037")
