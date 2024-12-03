#!/usr/bin/env python
import logging

from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.schema.network import (
    NetworkSchema,
)
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.run_test")


async def run_export_all(network_region_code: str | None = None) -> None:
    """
    Run energy exports for all regions or a specific network region if provided.

    This function retrieves the export map and filters energy exports by monthly priority.
    If a network region code is provided, it further filters the exports by that region.

    :param network_region_code: Optional network region code to filter exports.
    """
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    await export_energy(energy_exports.resources)


async def run_export_power_for_region(region_code: str) -> None:
    """
    Run power exports for a specific region.

    This function retrieves the export map and filters power exports by live priority
    and the specified region code.

    :param region_code: The region code to filter power exports.
    """
    export_map = get_export_map()
    power_exports = (
        export_map.get_by_stat_type(StatType.power).get_by_priority(PriorityType.live).get_by_network_region(region_code)
    )
    await export_power(power_exports.resources)


async def run_export_power_for_network(network: NetworkSchema) -> None:
    """
    Run power exports for a specific network.

    This function retrieves the export map and filters power exports by live priority
    and the specified network ID.

    :param network: The network schema object to filter power exports.
    """
    export_map = get_export_map()
    power_exports = export_map.get_by_stat_type(StatType.power).get_by_priority(PriorityType.live).get_by_network_id(network.code)
    await export_power(power_exports.resources)


async def run_export_energy_all(network_region_code: str | None = None) -> None:
    """
    Run energy exports for all regions or a specific network region if provided.

    This function retrieves the export map and filters energy exports by monthly priority.
    If a network region code is provided, it further filters the exports by that region.

    :param network_region_code: Optional network region code to filter exports.
    """
    export_map = get_export_map()
    energ_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)

    if network_region_code:
        energ_exports = energ_exports.get_by_network_region(network_region_code)

    await export_energy(energ_exports.resources)


async def run_export_energy_for_year(
    year: int | None = None, network_region_code: str | None = None, network: NetworkSchema | None = None
) -> None:
    """
    Run energy exports for a specific year for all regions or a specific network region or network if provided.

    This function retrieves the export map and filters energy exports by daily priority
    and the specified year. If a network region code or network is provided, it further filters the exports accordingly.

    :param year: The year to filter energy exports. Defaults to the current year.
    :param network_region_code: Optional network region code to filter exports.
    :param network: Optional network schema object to filter exports.
    """
    export_map = get_export_map()

    if not year:
        year = get_today_opennem().year

    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.daily).get_by_year(year)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    if network:
        energy_exports = energy_exports.get_by_network_id(network.code)

    logger.info(f"Running {len(energy_exports.resources)} exports")

    await export_energy(energy_exports.resources)
