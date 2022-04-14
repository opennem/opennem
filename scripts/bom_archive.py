#!/usr/bin/env python
"""
OpenNEM BoM Observation Archive Crawler

"""
import logging
import re
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlencode, urljoin
from zipfile import ZipFile

from opennem.core.loader import load_data
from opennem.utils.archive import _handle_zip, chain_streams, open
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

OUPUT_DIRECTORY = Path(__file__).parent.parent / "data/bom"


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


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
}


def bom_get_historic(station_code: str, obs_type: ObservationTypes) -> None:

    params = BOM_DIRECTORY_PARAMS.copy()
    params["p_stn_num"] = station_code
    params["p_nccObsCode"] = obs_type.value

    url = urljoin(BOM_BASE_URL, urlencode(params))

    r = http.get(BOM_BASE_URL, params=urlencode(params))

    if not r.ok:
        logger.error("Could not fetch url: {}".format(url))

    dc = _parse_directory(r.content)

    # Get observation

    directory_codes_fetched = []

    # if year not in dc.keys():
    # raise Exception("Could not find year {} for station {}".format(year, station_code))

    for directory_code in dc.values():

        if directory_code in directory_codes_fetched:
            continue

        params = BOM_RESOURCE_PARAMS.copy()
        params["p_stn_num"] = station_code
        params["p_c"] = directory_code

        r = http.get(BOM_BASE_URL, params=urlencode(params), headers=headers)

        if not r.ok:
            raise Exception("Url error in getting observation file")

        content = _unzip_content(r.content).decode("utf-8")

        if "Weather Data temporarily unavailable" in content:
            directory_codes_fetched.append(directory_code)
            logger.error("Could not get {}?{}".format(BOM_BASE_URL, urlencode(params)))
            continue

        file_name = "bom_{}_{}_{}.txt".format(
            station_code, obs_type.value, directory_code.lstrip("-")
        )

        with open(OUPUT_DIRECTORY / file_name, "w") as fh:
            fh.write(content)

        logger.info("Wrote file: {}".format(file_name))
        directory_codes_fetched.append(directory_code)


def import_station(station_code: str):
    pass


if __name__ == "__main__":
    bom_capitals = load_data("bom_capitals.json", from_project=True)

    for station_code in bom_capitals:
        for observation_type in [ObservationTypes.temp_min]:
            bom_get_historic(station_code, observation_type)
