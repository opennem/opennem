#!/usr/bin/env python
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from opennem import DATA_DIR_PATH
from opennem.core.parsers.aemo.filenames import parse_aemo_filename
from opennem.core.parsers.aemo.mms import parse_aemo_urls
from opennem.core.parsers.dirlisting import DirlistingEntryType, get_dirlisting

logger = logging.getLogger("opennem.mms.dirparser")

AEMO_BASE_URL = "https://nemweb.com.au/Reports/CURRENT/"

AEMO_MAP_PATH = DATA_DIR_PATH / "aemo_map.json"


@dataclass
class AEMOMMSMapSet:
    data: dict[str, Any] = field(default_factory=dict)
    found_files: list[str] = field(default_factory=list)


def parse_aemo_dirlisting(dirurl: str, mapset: AEMOMMSMapSet | None = None) -> AEMOMMSMapSet:
    if not mapset:
        mapset = AEMOMMSMapSet()

    dirlist = get_dirlisting(dirurl)

    for i in dirlist.entries:
        if i.entry_type == DirlistingEntryType.directory:
            if i.filename == Path("DUPLICATE"):
                continue

            parse_aemo_dirlisting(i.link, mapset=mapset)
            continue

        if i.filename.suffix.lower() not in [".zip", ".csv"]:
            logger.debug(f"Skipping: {i.filename}")
            continue

        try:
            t = parse_aemo_filename(str(i.filename))
        except Exception as e:
            logger.error(e)
            continue

        if t.filename in mapset.found_files:
            continue

        mapset.found_files.append(t.filename)

        try:
            ts = parse_aemo_urls([i.link])

            for table in ts.tables:
                if table.full_name not in mapset.data:
                    mapset.data[table.full_name] = table.__dict__

        except Exception as e:
            logger.error(e)

    return mapset


def sync_aemo_table_map() -> None:
    mms_map = parse_aemo_dirlisting(AEMO_BASE_URL)

    with open(AEMO_MAP_PATH, "w+") as fh:
        json.dump(mms_map.data, fh, indent=4, sort_keys=True, default=str)

    logger.info(f"Synced AEMO map to {AEMO_MAP_PATH}")


if __name__ == "__main__":
    sync_aemo_table_map()
