""" """
import logging
import os
from pathlib import Path

from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import parse_aemo_file
from opennem.utils.archive import download_and_unzip

logger = logging.getLogger("opennem.core.parsers.aemo.url")


def parse_aemo_url_optimized(url: str) -> int:
    """Optimized version of aemo url parser"""
    files_parsed = 0

    d = download_and_unzip(url)

    onlyfiles = [Path(d) / f for f in os.listdir(d) if (Path(d) / f).is_file()]
    logger.debug(f"Got {len(onlyfiles)} files")

    for f in onlyfiles:
        logger.info(f"parsing {f}")

        if f.suffix.lower() in [".csv"]:
            ts = parse_aemo_file(str(f))
            store_aemo_tableset(ts)
            files_parsed += 1

    return files_parsed
