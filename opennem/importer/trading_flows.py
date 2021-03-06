"""
    Create stations on NEM for import/export series
    and facility for one each of import/export
"""

import logging
from enum import Enum
from typing import List, Optional

from opennem.core.dispatch_type import DispatchType
from opennem.core.networks import state_from_network_region
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Location, Station
from opennem.diff.versions import get_network_regions
from opennem.schema.network import NetworkNEM, NetworkRegionSchema, NetworkSchema

logger = logging.getLogger("opennem.importer.trading_flows")


class FlowDirection(Enum):
    imports = "imports"
    exports = "exports"


def generated_flow_station_id(
    network: NetworkSchema,
    network_region: NetworkRegionSchema,
    flow_direction: Optional[FlowDirection] = None,
) -> str:
    name_components = [network.code, "flow", network_region.code]

    if flow_direction:
        name_components.append(flow_direction.value)

    name_components = [i.upper() for i in name_components]

    return "_".join(name_components)


