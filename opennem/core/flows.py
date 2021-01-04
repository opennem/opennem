from itertools import groupby
from operator import attrgetter
from typing import Dict, List

from opennem.api.stats.schema import DataQueryResult, RegionFlowResult


def net_flows(
    region: str, data: List[RegionFlowResult]
) -> Dict[str, List[DataQueryResult]]:
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

        for es in values:
            # @TODO this could be made neater

            if not es.generated:
                continue

            if es.flow_from == region:
                flow_set = "exports"

                if es.generated <= 0:
                    flow_set = "imports"

                output_set[k][flow_set] += es.generated

            if es.flow_to == region:
                flow_set = "imports"

                if es.generated <= 0:
                    flow_set = "exports"

                output_set[k][flow_set] += es.generated

    imports_list = []
    exports_list = []

    for interval, data in output_set.items():
        imports_list.append(
            DataQueryResult(
                interval=interval, group_by="imports", result=data["imports"]
            )
        )
        exports_list.append(
            DataQueryResult(
                interval=interval, group_by="exports", result=data["exports"]
            )
        )

    return {"imports": imports_list, "exports": exports_list}
