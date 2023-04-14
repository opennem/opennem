from datetime import datetime
from enum import Enum
from itertools import groupby
from operator import attrgetter

from datetime_truncate import truncate as date_trunc

from opennem.api.stats.schema import DataQueryResult, OpennemData, RegionFlowEmissionsResult, RegionFlowResult
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval


class FlowDirection(Enum):
    imports = "imports"
    exports = "exports"


def fueltech_to_flow(fueltech_id: str) -> FlowDirection | None:
    """Check if a fueltech is a flow and if so return the enum"""
    if not fueltech_id:
        raise Exception("Require a fueltech")

    ft = fueltech_id.lower()

    flow_directions = list(FlowDirection)

    for flow_direction in flow_directions:
        if flow_direction.value == ft:
            return flow_direction

    # shouldn't get here?!?
    return None


def generated_flow_station_id(
    network: NetworkSchema,
    network_region_code: str,
    flow_direction: FlowDirection | None = None,
) -> str:
    name_components = [network.code, "flow", network_region_code]

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

    if flow_set_inverted.code:
        flow_set_inverted.code = _invert_flowid(flow_set_inverted.code)

    def _save_invert(value: int | None) -> int | None:
        if value:
            return -value
        return None

    flow_set_inverted.history.data = [_save_invert(i) for i in flow_set.history.data]

    return flow_set_inverted


def net_flows(
    region: str,
    data: list[RegionFlowResult],
    interval: TimeInterval | None = None,
) -> dict[str, list[DataQueryResult]]:
    """
    Calculates net region flows for a region from a RegionFlowResult
    """

    def get_interval(flow_result: RegionFlowResult) -> datetime:
        value = flow_result.interval

        if interval:
            value = date_trunc(value, interval.trunc)

        return value

    data_net = []

    # group regular first for net flows per provided
    # period bucket from query
    for _k, v in groupby(data, attrgetter("interval")):
        values = list(v)

        fr = RegionFlowResult(
            interval=values[0].interval,
            flow_from="",
            flow_to="",
            flow_from_energy=0.0,
            flow_to_energy=0.0,
        )

        flow_sum = 0.0

        for es in values:
            if not es.generated:
                continue

            if es.flow_from == region:
                flow_sum += es.generated

            if es.flow_to == region:
                flow_sum += -1 * es.generated

        if flow_sum > 0:
            fr.flow_from_energy = flow_sum
        else:
            fr.flow_to_energy = flow_sum

        data_net.append(fr)

    output_set = {}

    # group interval second with provided interval
    for k, v in groupby(data_net, get_interval):
        values = list(v)

        if k not in output_set:
            output_set[k] = {
                "imports": 0.0,
                "exports": 0.0,
            }

        flow_sum_imports = 0.0
        flow_sum_exports = 0.0

        # Sum up
        for es in values:
            if es.flow_to_energy:
                flow_sum_imports += es.flow_to_energy

            if es.flow_from_energy:
                flow_sum_exports += es.flow_from_energy

        output_set[k]["imports"] = -1 * abs(flow_sum_imports) / 1000
        output_set[k]["exports"] = flow_sum_exports / 1000

    imports_list = []
    exports_list = []

    for interval, data in output_set.items():
        imports_list.append(DataQueryResult(interval=interval, group_by="imports", result=data["imports"]))
        exports_list.append(DataQueryResult(interval=interval, group_by="exports", result=data["exports"]))

    return {"imports": imports_list, "exports": exports_list}


def net_flows_emissions(
    region: str,
    data: list[RegionFlowEmissionsResult],
    interval: TimeInterval,
) -> dict[str, list[DataQueryResult]]:
    """
    Calculates net region flow emissions for a region from a RegionFlowResult
    """

    output_set = {}

    for k, v in groupby(data, lambda x: date_trunc(x.interval, interval.trunc)):
        values = list(v)

        if k not in output_set:
            output_set[k] = {
                "imports": 0.0,
                "exports": 0.0,
            }

        export_emissions_sum = 0.0
        import_emissions_sum = 0.0

        # Sum up
        for es in values:
            if not es.flow_from:
                continue

            if es.flow_from == region:
                if es.energy and es.energy > 0:
                    if es.flow_from_intensity:
                        export_emissions_sum += abs(es.flow_from_emissions)
                else:
                    if es.flow_to_emissions:
                        import_emissions_sum += abs(es.flow_to_emissions)

            if es.flow_to == region:
                if es.energy and es.energy < 0:
                    if es.flow_from_emissions:
                        export_emissions_sum += abs(es.flow_from_emissions)
                else:
                    if es.flow_to_emissions:
                        import_emissions_sum += abs(es.flow_to_emissions)

        # @NOTE matching on 30m intervals not 1h so divide
        output_set[k]["imports"] = import_emissions_sum / 2
        output_set[k]["exports"] = export_emissions_sum / 2

    imports_list = []
    exports_list = []

    for interval, data in output_set.items():
        imports_list.append(DataQueryResult(interval=interval, group_by="imports", result=data["imports"]))
        exports_list.append(DataQueryResult(interval=interval, group_by="exports", result=data["exports"]))

    return {"imports": imports_list, "exports": exports_list}
