"""Record queries only read a network's own regions.

A network is selected by network_id plus its subnetworks, and the OPENNEM_ROOFTOP_BACKFILL
subnetwork carries NT1 rooftop (2015-10 to 2016-08). That minted au.nem.nt1.* record chains and
added NT rooftop into NEM totals. Both detection paths now keep to the declared regions plus the
historic ones (SNOWY1 for the NEM).
"""

from datetime import datetime

import pytest

from opennem.recordreactor.backlog import GroupingConfig, _analyze_milestone_records
from opennem.recordreactor.metric_registry import get_metric_registry, get_network_region_filter_sql
from opennem.recordreactor.queries_incremental import build_period_aggregation_query
from opennem.recordreactor.schema import MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM, NetworkWEM

NEM_FILTER = "network_region IN ('NSW1','QLD1','SA1','TAS1','VIC1','SNOWY1')"


class _QueryCapturingClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list:
        self.queries.append(query)
        return []


def _normalise(sql: str) -> str:
    return sql.replace(", ", ",").replace("' ,'", "','")


def test_nem_filter_keeps_declared_and_historic_regions() -> None:
    sql = _normalise(get_network_region_filter_sql(NetworkNEM))

    assert NEM_FILTER in sql
    assert "NT1" not in sql


def test_wem_filter_is_its_single_region() -> None:
    assert "'WEM'" in get_network_region_filter_sql(NetworkWEM)


@pytest.mark.parametrize(
    "grouping",
    [
        GroupingConfig(name="network", group_by_fields=[]),
        GroupingConfig(name="region", group_by_fields=["network_region"]),
        GroupingConfig(name="region_fueltech", group_by_fields=["network_region", "fueltech_group_id"]),
    ],
)
def test_backlog_base_stats_filters_regions(grouping: GroupingConfig) -> None:
    client = _QueryCapturingClient()
    _analyze_milestone_records(
        client=client,  # type: ignore[arg-type]
        network=NetworkNEM,
        period=MilestonePeriod.day,
        milestone_type=MilestoneType.energy,
        grouping=grouping,
        end_date=datetime(2026, 9, 22),
    )

    assert NEM_FILTER in _normalise(client.queries[0])


def test_incremental_query_filters_regions() -> None:
    metric_def = next(m for m in get_metric_registry() if m.metric == MilestoneType.energy)
    sql = build_period_aggregation_query(
        metric_def=metric_def,
        network=NetworkNEM,
        grouping=GroupingConfig(name="region", group_by_fields=["network_region"]),
        period=MilestonePeriod.day,
        period_start=datetime(2026, 9, 21),
        period_end=datetime(2026, 9, 22),
    )

    assert NEM_FILTER in _normalise(sql)
