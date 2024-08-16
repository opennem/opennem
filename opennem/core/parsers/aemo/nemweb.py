"""NEMWeb optimized parsers"""

import logging
from shutil import rmtree

from opennem.controllers.nem import store_aemo_tableset
from opennem.controllers.schema import ControllerReturn
from opennem.core.parsers.aemo.mms import AEMOTableSet, parse_aemo_file
from opennem.utils.archive import download_and_unzip

logger = logging.getLogger("opennem.core.parsers.aemo.nemweb")


async def parse_aemo_url_optimized(
    url: str, table_set: AEMOTableSet | None = None, persist_to_db: bool = True, values_only: bool = False
) -> ControllerReturn | AEMOTableSet:
    """Optimized version of aemo url parser that stores the files locally in tmp
    and parses them individually to resolve memory pressure"""
    download_path = download_and_unzip(url)
    cr = ControllerReturn()

    download_path_files = [f for f in download_path.iterdir() if f.is_file()]

    logger.debug(f"Got {len(download_path_files)} files")

    if not table_set:
        table_set = AEMOTableSet()

    for csv_file_to_process in download_path_files:
        logger.info(f"parsing {csv_file_to_process}")

        if csv_file_to_process.suffix.lower() != ".csv":
            continue

        table_set = parse_aemo_file(str(csv_file_to_process), table_set=table_set, values_only=values_only)

        if persist_to_db:
            controller_returns = await store_aemo_tableset(table_set)
            cr.inserted_records += controller_returns.inserted_records

            if cr.last_modified and controller_returns.last_modified and cr.last_modified < controller_returns.last_modified:
                cr.last_modified = controller_returns.last_modified

        try:
            csv_file_to_process.unlink()
        except Exception as e:
            logger.error(f"Error removing file {csv_file_to_process}: {e}")

    if not persist_to_db:
        return table_set

    try:
        rmtree(download_path)
        logger.info(f"Removed {download_path}")
    except Exception as e:
        logger.error(f"Error removing download path: {e}")

    return cr


async def parse_aemo_url_optimized_bulk(
    url: str, table_set: AEMOTableSet | None = None, persist_to_db: bool = True
) -> ControllerReturn | AEMOTableSet:
    """Optimized version of aemo url parser that stores the files locally in tmp
    and parses them individually to resolve memory pressure"""
    download_path = download_and_unzip(url)
    cr = ControllerReturn()

    download_path_files = [f for f in download_path.iterdir() if f.is_file()]
    logger.debug(f"Got {len(download_path_files)} files")

    ts = AEMOTableSet()

    for f in download_path_files:
        logger.info(f"parsing {f}")

        if f.suffix.lower() != ".csv":
            continue

        ts = parse_aemo_file(str(f), table_set=ts)

        if not persist_to_db:
            return ts

    controller_returns = store_aemo_tableset(ts)
    cr.inserted_records += controller_returns.inserted_records

    if cr.last_modified and controller_returns.last_modified and cr.last_modified < controller_returns.last_modified:
        cr.last_modified = controller_returns.last_modified

    try:
        rmtree(download_path)
        logger.info(f"Removed {download_path}")
    except Exception as e:
        logger.error(f"Error removing download path: {e}")

    return cr


# debug entry point
if __name__ == "__main__":
    # @TODO parse into MMS schema
    url = "https://nemweb.com.au/Reports/ARCHIVE/TradingIS_Reports/PUBLIC_TRADINGIS_20231231_20240106.zip"
    # parse_aemo_url_optimized(url)
    import asyncio

    asyncio.run(parse_aemo_url_optimized(url))

    # controller_returns = store_aemo_tableset(r)
