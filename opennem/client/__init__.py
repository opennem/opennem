"""
OpenNEM API Client

(c) 2021 - Opennem Inc.
"""

from typing import Optional

from opennem.api.stats.schema import (
    DataQueryResult,
    OpennemDataSet,
    RegionFlowResult,
    ScadaDateRange,
)
from opennem.schema.network import NetworkSchema
from opennem.settings.schema import OpennemSettings
from opennem.utils.http import http


class OpennemClient:

    _http = None

    def __init__(self, settings: Optional[OpennemSettings] = None) -> None:
        self._http = http
        pass

    def get_networks() -> None:
        pass


def main() -> None:
    co = OpennemDataSet()

    co.append_set()

    return None


if __name__ == "__main__":
    pass
