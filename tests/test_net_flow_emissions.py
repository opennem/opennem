import csv
from pathlib import Path
from typing import Dict, List

import pytest

from opennem.api.stats.schema import RegionFlowEmissionsResult
from opennem.api.time import human_to_interval
from opennem.core.flows import net_flows_emissions


def get_test_fixture(filename: str) -> List[Dict]:
    csv_fixture = Path(__file__).parent / "fixtures" / filename

    if not csv_fixture.is_file():
        raise Exception("not a file")

    records = []

    with csv_fixture.open() as fh:
        csvreader = csv.DictReader(fh)

        for r in csvreader:
            records.append(r)

    return records


def test_nem_nsw1_201512() -> None:
    query_result = get_test_fixture("emissions_nem_nsw1_201512.csv")

    region_flows = [
        RegionFlowEmissionsResult(
            interval=i["trading_interval"],
            flow_from=i["flow_from"],
            flow_to=i["flow_to"],
            energy=i["energy"],
            flow_from_emissions=i["flow_from_emissions"],
            flow_to_emissions=i["flow_to_emissions"],
        )
        for i in query_result
    ]

    interval = human_to_interval("1M")

    flows = net_flows_emissions("NSW1", region_flows, interval)

    print(flows)


if __name__ == "__main__":
    test_nem_nsw1_201512()
