from itertools import groupby
from operator import attrgetter
from typing import Dict, List

from opennem.api.stats.schema import DataQueryResult, RegionFlowResult


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
