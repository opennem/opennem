from enum import Enum
from typing import Optional

from opennem.api.stats.schema import OpennemData
from opennem.schema.network import NetworkRegionSchema, NetworkSchema


class FlowDirection(Enum):
    imports = "imports"
    exports = "exports"


def fueltech_to_flow(fueltech_id: str) -> Optional[FlowDirection]:
    """Check if a fueltech is a flow and if so return the enum"""
    if not fueltech_id:
        raise Exception("Require a fueltech")

    ft = fueltech_id.lower()

    flow_directions = [i for i in FlowDirection]

    for flow_direction in flow_directions:
        if flow_direction.value == ft:
            return flow_direction

    # shouldn't get here?!?
    return None


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


def _invert_flowid(flowid: str) -> str:
    """Reverses the flow id"""
    return "->".join(flowid.split("->")[::-1])


def invert_flow_set(flow_set: OpennemData) -> OpennemData:
    """Takes a flow like NSW1->QLD1 and inverts it to QLD1->NSW1"""
    flow_set_inverted = flow_set.copy()

    if flow_set.id:
        id_comps = flow_set.id.split(".")
        id_comps_out = []

        for _id in id_comps:
            if "->" in _id:
                _id = _invert_flowid(_id)
            id_comps_out.append(_id)

        new_id = ".".join(id_comps_out)

        flow_set_inverted.id = new_id

    if flow_set_inverted.region:
        flow_set_inverted.region = _invert_flowid(flow_set_inverted.region)

    def _save_invert(value: Optional[int]) -> Optional[int]:
        if value:
            return -value
        return None

    flow_set_inverted.history.data = [_save_invert(i) for i in flow_set.history.data]

    return flow_set_inverted
