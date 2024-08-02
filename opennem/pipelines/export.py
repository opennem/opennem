"""
Export pipeline

@NOTE these are new optimized version of what was in opennem.api.export.tasks
that run per-interval and eventually per-day

ie. replace the export sets and export_power and export_energy which was all
a bit too abstract.
"""

import logging

from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.schema.network import NetworkSchema
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.pipelines.export")


async def run_export_power_latest_for_network(network: NetworkSchema, network_region_code: str | None = None) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    latest_power_exports = (
        export_map.get_by_stat_type(StatType.power).get_by_priority(PriorityType.live).get_by_network_id(network.code)
    )

    if network_region_code:
        latest_power_exports = latest_power_exports.get_by_network_region(network_region_code)

    logger.info(f"Running {len(latest_power_exports.resources)} exports")

    await export_power(stats=latest_power_exports.resources)


async def run_export_all(network_region_code: str | None = None) -> None:
    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    await export_energy(energy_exports.resources)


async def run_export_power_for_region(region_code: str) -> None:
    # run exports for all
    export_map = get_export_map()
    power_exports = (
        export_map.get_by_stat_type(StatType.power).get_by_priority(PriorityType.live).get_by_network_region(region_code)
    )
    await export_power(power_exports.resources)


async def run_export_current_year(network_region: str | None = None) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    current_year = get_today_opennem().year

    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.daily).get_by_year(current_year)

    if network_region:
        energy_exports = energy_exports.get_by_network_region(network_region)

    logger.info(f"Running {len(energy_exports.resources)} exports")
    await export_energy(energy_exports.resources)
