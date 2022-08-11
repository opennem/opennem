""" NEMWeb optimized parsers """

import logging
import os
from pathlib import Path

from opennem.controllers.nem import store_aemo_tableset
from opennem.controllers.schema import ControllerReturn
from opennem.core.parsers.aemo.mms import AEMOTableSet, parse_aemo_file
from opennem.utils.archive import download_and_unzip

logger = logging.getLogger("opennem.core.parsers.aemo.nemweb")


def parse_aemo_url_optimized(
    url: str, table_set: AEMOTableSet | None = None, persist_to_db: bool = True, values_only: bool = False
) -> ControllerReturn | AEMOTableSet:
    """Optimized version of aemo url parser that stores the files locally in tmp
    and parses them individually to resolve memory pressure"""
    d = download_and_unzip(url)
    cr = ControllerReturn()

    onlyfiles = [Path(d) / f for f in os.listdir(d) if (Path(d) / f).is_file()]
    logger.debug(f"Got {len(onlyfiles)} files")

    if not table_set:
        table_set = AEMOTableSet()

    for f in onlyfiles:
        logger.info(f"parsing {f}")

        if f.suffix.lower() not in [".csv"]:
            continue

        table_set = parse_aemo_file(str(f), table_set=table_set, values_only=values_only)

        if persist_to_db:
            controller_returns = store_aemo_tableset(table_set)
            cr.inserted_records += controller_returns.inserted_records

            if (
                cr.last_modified
                and controller_returns.last_modified
                and cr.last_modified < controller_returns.last_modified
            ):
                cr.last_modified = controller_returns.last_modified

    if not persist_to_db:
        return table_set

    return cr


def parse_aemo_url_optimized_bulk(
    url: str, table_set: AEMOTableSet | None = None, persist_to_db: bool = True
) -> ControllerReturn | AEMOTableSet:
    """Optimized version of aemo url parser that stores the files locally in tmp
    and parses them individually to resolve memory pressure"""
    d = download_and_unzip(url)
    cr = ControllerReturn()

    onlyfiles = [Path(d) / f for f in os.listdir(d) if (Path(d) / f).is_file()]
    logger.debug(f"Got {len(onlyfiles)} files")

    ts = AEMOTableSet()

    for f in onlyfiles:
        logger.info(f"parsing {f}")

        if f.suffix.lower() not in [".csv"]:
            continue

        ts = parse_aemo_file(str(f), table_set=ts)

        if not persist_to_db:
            return ts

    controller_returns = store_aemo_tableset(ts)
    cr.inserted_records += controller_returns.inserted_records

    if cr.last_modified and controller_returns.last_modified and cr.last_modified < controller_returns.last_modified:
        cr.last_modified = controller_returns.last_modified

    return cr


# debug entry point
if __name__ == "__main__":
    # @TODO parse into MMS schema
    # url = "https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/PUBLIC_DISPATCHIS_20220612.zip"
    url = "https://nemweb.com.au/Reports/ARCHIVE/TradingIS_Reports/PUBLIC_TRADINGIS_20210620_20210626.zip"
    parse_aemo_url_optimized(url)

    # controller_returns = store_aemo_tableset(r)
