#!/usr/bin/env python
import logging
from datetime import datetime

from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.api.stats.schema import load_opennem_dataset_from_url

logger = logging.getLogger("opennem.run_test")

CURRENT_YEAR = datetime.now().year


def run_export_all(network_region_code: str | None = None) -> None:
    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    export_energy(energy_exports.resources)


def run_export_power_for_region(region_code: str) -> None:
    # run exports for all
    export_map = get_export_map()
    power_exports = (
        export_map.get_by_stat_type(StatType.power)
        .get_by_priority(PriorityType.live)
        .get_by_network_region(region_code)
    )
    export_power(power_exports.resources)


def run_export_current_year(network_region: str) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    energy_exports = (
        export_map.get_by_stat_type(StatType.energy)
        .get_by_priority(PriorityType.daily)
        .get_by_year(CURRENT_YEAR)
        .get_by_network_region(network_region)
    )
    logger.info(f"Running {len(energy_exports.resources)} exports")
    export_energy(energy_exports.resources)


def run_export_energy_for_region(region_code: str) -> None:
    # run exports for all
    export_map = get_export_map()
    energ_exports = (
        export_map.get_by_stat_type(StatType.energy)
        .get_by_priority(PriorityType.monthly)
        .get_by_network_region(region_code)
    )
    export_energy(energ_exports.resources)


def run_weekly() -> None:
    pass


def test_ids() -> None:
    u = "https://data.opennem.org.au/v3/stats/au/all/monthly.json"

    ds = load_opennem_dataset_from_url(u)
    ids = [series.id for series in ds.data if series.id]

    unique_ids = list(set(ids))

    print(f"have {len(ids)} ids and {len(unique_ids)} unique ids")

    if len(ids) - len(unique_ids) != 0:
        print("ERROR: duplicate ids")

        duplicate_ids = list(set(ids) - set(unique_ids))
        for i in duplicate_ids:
            print(i)


if __name__ == "__main__":
    # run_export_all()
    # export_all_daily()
    # export_energy(latest=True)
    # run_export_all()
    # run_export_power_for_region("NSW1")
    # export_all_monthly()
    # export_all_daily()
    # export_all_monthly()
    # test_ids()
    # export_energy(latest=True)

    # run_flow_updates_all_per_year
    run_export_current_year("NSW1")

    # run_flow_updates_all_per_year(2009, 1)
    # run_flow_updates_all_per_year(2010, 1)
    # run_flow_updates_all_per_year(2015, 1)
    # run_flow_updates_all_per_year(2019, 1)
    # run_flow_updates_all_per_year(2020, 1)
    # run_flow_updates_all_per_year(2021, 1)
    # run_flow_updates_all_per_year(2022, 1)
    # run_flow_updates_all_for_network(NetworkNEM)
    # run_export_current_year("NSW1")
    # export_energy(latest=True)
    # export_power()
    # run_export_energy_for_region("NSW1")
