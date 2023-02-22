"""
Export pipeline
"""
import logging

from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_power
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.pipelines.export")


def run_export_power_latest_for_network(network: NetworkSchema, network_region_code: str | None = None) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    latest_power_exports = (
        export_map.get_by_stat_type(StatType.power).get_by_priority(PriorityType.live).get_by_network_id(network.code)
    )

    if network_region_code:
        latest_power_exports = latest_power_exports.get_by_network_region(network_region_code)

    logger.info(f"Running {len(latest_power_exports.resources)} exports")

    export_power(stats=latest_power_exports.resources)
