"""
OpenNEM API Client

(c) 2020 - Opennem Inc.
"""

from opennem.api.stats.schema import (
    DataQueryResult,
    OpennemDataSet,
    RegionFlowResult,
    ScadaDateRange,
)


def main() -> None:
    co = OpennemDataSet()

    co.append_set()

    return None


if __name__ == "__main__":
    pass
