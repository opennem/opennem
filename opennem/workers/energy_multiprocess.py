"""
Multiprocessor for energy workers

"""
import logging
import multiprocessing
from datetime import datetime
from typing import List, Tuple

from opennem.diff.versions import CUR_YEAR, get_network_regions
from opennem.schema.network import NetworkNEM
from opennem.workers.energy import run_energy_update_archive

logger = logging.getLogger("opennem.worker.energy_multi")

CPU_COUNT = multiprocessing.cpu_count()
WORKER_COUNT = int(CPU_COUNT / 3)
YEAR_EARLIEST = 2020
CUR_MONTH = datetime.now().month


def _build_args_list() -> List[Tuple[int, int, str]]:
    args_list = []

    network = NetworkNEM
    regions = [i.code for i in get_network_regions(network)]

    for year in range(CUR_YEAR, YEAR_EARLIEST - 1, -1):
        for month in range(12, 0, -1):
            for region in regions:
                if year == CUR_YEAR and month > CUR_MONTH:
                    continue

                args_list.append((year, month, region))

    return args_list


def _worker_wrap(year, months, region):
    """Map to named args"""
    return run_energy_update_archive(
        year=year, months=[months], regions=[region], fueltech_id="exports"
    )


def energy_process() -> None:
    args_list = _build_args_list()
    logger.debug("Starting with {} workers".format(WORKER_COUNT))

    with multiprocessing.Pool(processes=WORKER_COUNT) as pool:
        pool.starmap(_worker_wrap, args_list)


if __name__ == "__main__":
    energy_process()
