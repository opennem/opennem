from datetime import datetime
from itertools import groupby
from operator import attrgetter
from typing import Dict, List, Optional

from datetime_truncate import truncate

from opennem.api.stats.schema import DataQueryResult, RegionFlowEmissionsResult, RegionFlowResult
from opennem.schema.time import TimeInterval


def net_flows(
    region: str,
    data: List[RegionFlowResult],
    interval: Optional[TimeInterval] = None,
) -> Dict[str, List[DataQueryResult]]:
    """
    Calculates net region flows for a region from a RegionFlowResult
    """

    def get_interval(flow_result: RegionFlowResult) -> datetime:
        value = flow_result.interval

        if interval:
            value = truncate(value, interval.trunc)

        return value

    data_net = []

    # group regular first for net flows per provided
    # period bucket from query
    for k, v in groupby(data, attrgetter("interval")):
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
        imports_list.append(
            DataQueryResult(interval=interval, group_by="imports", result=data["imports"])
        )
        exports_list.append(
            DataQueryResult(interval=interval, group_by="exports", result=data["exports"])
        )

    return {"imports": imports_list, "exports": exports_list}


def net_flows_emissions(
    region: str,
    data: List[RegionFlowEmissionsResult],
    interval: TimeInterval,
) -> Dict[str, List[DataQueryResult]]:
    """
    Calculates net region flow emissions for a region from a RegionFlowResult
    """

    output_set = {}

    for k, v in groupby(data, lambda x: truncate(x.interval, interval.trunc)):
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
                if es.energy > 0:
                    if es.flow_from_intensity:
                        export_emissions_sum += abs(es.flow_from_emissions)
                else:
                    if es.flow_to_emissions:
                        import_emissions_sum += abs(es.flow_to_emissions)

            if es.flow_to == region:
                if es.energy < 0:
                    if es.flow_from_emissions:
                        export_emissions_sum += abs(es.flow_from_emissions)
                else:
                    if es.flow_to_emissions:
                        import_emissions_sum += abs(es.flow_to_emissions)

        output_set[k]["imports"] = import_emissions_sum
        output_set[k]["exports"] = export_emissions_sum

    imports_list = []
    exports_list = []

    for interval, data in output_set.items():
        imports_list.append(
            DataQueryResult(interval=interval, group_by="imports", result=data["imports"])
        )
        exports_list.append(
            DataQueryResult(interval=interval, group_by="exports", result=data["exports"])
        )

    return {"imports": imports_list, "exports": exports_list}
