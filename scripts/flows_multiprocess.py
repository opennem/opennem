#!/usr/bin/env python
import logging
import multiprocessing
from datetime import datetime, timedelta, timezone
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem import settings
from opennem.aggregates.network_flows_v3 import (
    run_aggregate_flow_for_interval_v3,
)
from opennem.api.export.tasks import export_all_daily, export_all_monthly
from opennem.api.export.tasks import export_energy, export_power
from opennem.schema.network import (
    NetworkNEM,
)
from opennem.utils.dates import get_last_complete_day_for_network, month_series

logger = logging.getLogger("opennem.run_test")

CURRENT_YEAR = datetime.now().year
NEM_LATEST_DATE = get_last_complete_day_for_network(NetworkNEM)


def run_export_for_year(year: int, network_region_code: str | None = None) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.daily).get_by_year(year)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    logger.info(f"Running {len(energy_exports.resources)} exports")

    export_energy(energy_exports.resources)


def run_flows_for_month(interval_start: datetime, interval_end: datetime) -> None:
    if interval_start > NEM_LATEST_DATE:
        logger.error(f"Got out of range start date {interval_start}")
        return None

    if interval_end > NEM_LATEST_DATE:
        interval_end = NEM_LATEST_DATE

    logger.info(f"Running for {interval_start} to {interval_end}")

    if not settings.dry_run:
        run_aggregate_flow_for_interval_v3(
            network=NetworkNEM,
            interval_start=interval_start,
            interval_end=interval_end,
        )


def run_multiprocess_flows(proprtion_of_cores: float = 0.5) -> None:
    use_cores = int(round(multiprocessing.cpu_count() * proprtion_of_cores, 0))
    logger.info(f"Number of cpus used : {use_cores}")

    work_args = []
    period_end = datetime.fromisoformat("2022-01-01T00:00:00").date()
    period_start = datetime.fromisoformat("2022-12-01T00:00:00").date()

    for interval_start in month_series(period_start, period_end, reverse=False):
        next_month = interval_start.replace(day=28) + timedelta(days=4)
        interval_end = next_month - timedelta(days=next_month.day) + timedelta(days=1) - timedelta(seconds=1)

        interval_start = interval_start.replace(tzinfo=timezone(timedelta(hours=10)))
        interval_end = interval_end.replace(tzinfo=timezone(timedelta(hours=10)))

        work_args.append((interval_start, interval_end))

    with multiprocessing.Pool(processes=use_cores) as p:
        p.starmap(run_flows_for_month, work_args)


def catchup_outputs() -> None:
    CURRENT_YEAR = datetime.now().year

    export_energy(latest=True)
    #  run exports for last year
    run_export_for_year(CURRENT_YEAR - 1)
    export_power()

    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)
    export_energy(energy_exports.resources)

    export_all_daily()
    export_all_monthly()


if __name__ == "__main__":
    run_multiprocess_flows()

    if not settings.dry_run:
        catchup_outputs()
