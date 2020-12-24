from itertools import groupby
from operator import attrgetter
from typing import List

from opennem.api.stats.schema import DataQueryResult, RegionFlowResult


def net_flows(region: str, data: RegionFlowResult) -> List[DataQueryResult]:
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

        output_set[k] = values
        print(values)

    imports_list = []

    for interval, data in output_set.items():
        imports_list.append(
            DataQueryResult(interval=interval, result=data["imports"])
        )

    return imports_list
