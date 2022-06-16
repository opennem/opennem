#!/usr/bin/env python
import json
import logging
from pathlib import Path

from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.filenames import parse_aemo_filename
from opennem.core.parsers.aemo.mms import parse_aemo_mms_csv, parse_aemo_urls
from opennem.core.parsers.dirlisting import DirlistingEntryType, get_dirlisting
from opennem.utils.http import http

logger = logging.getLogger("opennem.mms.dirparser")

AEMO_BASE_URL = "https://nemweb.com.au/Reports/CURRENT/"


def check_tableset() -> None:
    # @TODO parse into MMS schema
    url = (
        "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_202204081455_0000000360913773.zip"
    )

    r = parse_aemo_urls([url])
    assert r.has_table("unit_scada"), "has table"

    print("has table and done")

    controller_returns = store_aemo_tableset(r)


AEMO_MMS_MAP = {}


def parse_aemo_dirlisting(dirurl: str) -> None:

    try:
        dirlist = get_dirlisting(dirurl)
    except Exception as e:
        logger.error(f"Error download {dirurl}")
        logger.debug(e)
        return None

    count = 0

    for i in dirlist.entries:
        if count >= 10:
            break

        if i.entry_type == DirlistingEntryType.directory:
            if i.filename == Path("DUPLICATE"):
                continue

            parse_aemo_dirlisting(i.link)
            continue

        if i.filename.suffix.lower() != ".zip":
            continue

        try:
            t = parse_aemo_filename(str(i.filename))
        except Exception as e:
            logger.error(e)
            continue

        if t.filename in AEMO_MMS_MAP:
            continue

        try:
            AEMO_MMS_MAP[t.filename] = parse_aemo_urls([i.link]).__dict__
            count += 1
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    parse_aemo_dirlisting(AEMO_BASE_URL)

    with open("mms.json", "w+") as fh:
        json.dump(AEMO_MMS_MAP, fh, indent=4, sort_keys=True, default=str)

    print("wrote da file it was mad")
