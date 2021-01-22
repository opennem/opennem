from itertools import groupby
from operator import attrgetter
from typing import Dict, List

from datetime_truncate import truncate

from opennem.api.stats.schema import DataQueryResult, RegionFlowEmissionsResult, RegionFlowResult
from opennem.schema.time import TimeInterval


def net_flows(region: str, data: List[RegionFlowResult]) -> Dict[str, List[DataQueryResult]]:
    """
    Calculates net region flows for a region from a RegionFlowResult
    """

    output_set = {}

    for k, v in groupby(data, attrgetter("interval")):
        values = list(v)

        if k not in output_set:
            output_set[k] = {
                "imports": 0.0,
                "exports": 0.0,
            }

        flow_sum = 0.0
        flow_type = "imports"

        # Sum up
        for es in values:

            if not es.generated:
                continue

            if es.flow_from == region:
                flow_sum += es.generated

            if es.flow_to == region:
                flow_sum += -1 * es.generated

        if flow_sum > 0:
            flow_type = "exports"

        output_set[k][flow_type] = flow_sum

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
    interval: TimeInterval, region: str, data: List[RegionFlowEmissionsResult]
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

        flow_sum = 0.0
        flow_type = "imports"

        # Sum up
        for es in values:

            if not es.flow_from:
                continue

            if es.flow_from == region:
                flow_sum += es.flow_from_emissions

            if es.flow_to == region:
                flow_sum += es.flow_to_emissions

        if flow_sum > 0:
            flow_type = "exports"

        output_set[k][flow_type] = flow_sum

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
