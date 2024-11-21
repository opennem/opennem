#!/usr/bin/env python
import logging
from datetime import datetime

from opennem import settings
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.schema.network import (
    NetworkSchema,
)

logger = logging.getLogger("opennem.run_test")

CURRENT_YEAR = datetime.now().year


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


async def run_export_power_for_network(network: NetworkSchema) -> None:
    # run exports for all
    export_map = get_export_map()
    power_exports = export_map.get_by_stat_type(StatType.power).get_by_priority(PriorityType.live).get_by_network_id(network.code)
    await export_power(power_exports.resources)


async def run_export_current_year(network_region_code: str | None = None) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.daily).get_by_year(CURRENT_YEAR)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    logger.info(f"Running {len(energy_exports.resources)} exports")

    if not settings.dry_run:
        await export_energy(energy_exports.resources)


async def run_export_energy_all(network_region_code: str | None = None) -> None:
    # run exports for all
    export_map = get_export_map()
    energ_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)

    if network_region_code:
        energ_exports = energ_exports.get_by_network_region(network_region_code)

    await export_energy(energ_exports.resources)


async def run_export_energy_for_year(
    year: int, network_region_code: str | None = None, network: NetworkSchema | None = None
) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.daily).get_by_year(year)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    if network:
        energy_exports = energy_exports.get_by_network_id(network.code)

    logger.info(f"Running {len(energy_exports.resources)} exports")

    await export_energy(energy_exports.resources)
