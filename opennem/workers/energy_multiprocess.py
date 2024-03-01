"""
Multiprocessor for energy workers

"""

import logging
import multiprocessing
import sys
from datetime import datetime

import click

from opennem.core.facility.fueltechs import load_fueltechs
from opennem.diff.versions import CUR_YEAR, get_network_regions
from opennem.schema.network import NetworkNEM
from opennem.workers.energy import run_energy_update_archive

logger = logging.getLogger("opennem.worker.energy_multi")

CPU_COUNT = multiprocessing.cpu_count()
WORKER_COUNT = 2
YEAR_EARLIEST = 2020
CUR_MONTH = datetime.now().month


def _build_args_list(
    year: int | None, region: str | None, fueltech: str | None
) -> list[tuple[int | None, int, str | None, str | None]]:
    args_list = []

    network = NetworkNEM

    regions = [region]

    if not region:
        regions = [i.code for i in get_network_regions(network)]

    fueltechs = [fueltech]

    if not fueltech:
        fueltechs = list(load_fueltechs().keys())

    years = [year]

    if not year:
        years = list(range(CUR_YEAR, YEAR_EARLIEST - 1, -1))

    for year in years:
        for month in range(12, 0, -1):
            if year == CUR_YEAR and month > CUR_MONTH:
                continue

            for region in regions:
                if year == CUR_YEAR and month > CUR_MONTH:
                    continue

                for ft in fueltechs:
                    args_list.append((year, month, region, ft))

    return args_list


def _worker_wrap(year: int | None, months: int, region: str, fueltech_id: str | None) -> None:
    """Map to named args"""
    return run_energy_update_archive(year=year, months=[months], regions=[region], fueltech=fueltech_id)


def energy_process(args_list: list, worker_count: int | None) -> None:
    logger.debug(f"Starting with {WORKER_COUNT} workers")

    if not worker_count:
        worker_count = WORKER_COUNT

    with multiprocessing.Pool(processes=worker_count) as pool:
        pool.starmap(_worker_wrap, args_list)


@click.command()
@click.option("--year", required=False, type=int)
@click.option("--workers", required=False, type=int)
@click.option("--fueltech", required=False, type=str)
@click.option("--region", required=False, type=str)
def cli(
    year: int | None = None,
    fueltech: str | None = None,
    region: str | None = None,
    workers: int | None = None,
) -> None:
    args_list = _build_args_list(year=year, region=region, fueltech=fueltech)
    click.echo(f"Running {len(args_list)} items")
    energy_process(args_list, worker_count=workers)


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        logger.error("User stopped")
        sys.exit(-1)
    except Exception as e:
        logger.error(e)
