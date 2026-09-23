"""Regression guard for #653: nem-wide demand must be summed, not averaged.

`market_summary` holds exactly one row per (interval, network_region). The network grouping has no
region key, so AVG(demand) returned the mean of the five NEM regions and
`au.nem.demand.power.interval.low` published 1,820 MW when NEM demand was 9,100 MW — exactly 5x
out. Day+ already summed demand_energy.

Price is deliberately left on AVG: the mean across regions is the intended definition there.
"""

from datetime import datetime

from opennem.recordreactor.backlog import GroupingConfig as BacklogGrouping
from opennem.recordreactor.backlog import _analyze_milestone_records
from opennem.recordreactor.metric_registry import (
    GROUPING_NETWORK,
    GROUPING_REGION,
    get_metric_registry,
    get_value_expression,
)
from opennem.recordreactor.queries_incremental import build_period_aggregation_query
from opennem.recordreactor.schema import MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM

DEMAND_METRIC = next(m for m in get_metric_registry() if m.metric == MilestoneType.demand)
PRICE_METRIC = next(m for m in get_metric_registry() if m.metric == MilestoneType.price)


class _QueryCapturingClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list:
        self.queries.append(query)
        return []


def _backlog_query(milestone_type: MilestoneType, period: MilestonePeriod) -> str:
    client = _QueryCapturingClient()
    _analyze_milestone_records(
        client=client,  # type: ignore[arg-type]
        network=NetworkNEM,
        period=period,
        milestone_type=milestone_type,
        grouping=BacklogGrouping(name="network", group_by_fields=[]),
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2026, 1, 1),
    )
    assert len(client.queries) == 1
    return client.queries[0]


def test_demand_interval_value_expression_is_sum() -> None:
    assert get_value_expression(DEMAND_METRIC, MilestonePeriod.interval) == ("demand", "SUM")


def test_demand_day_and_above_value_expression_is_sum() -> None:
    for period in (MilestonePeriod.day, MilestonePeriod.month, MilestonePeriod.quarter, MilestonePeriod.year):
        assert get_value_expression(DEMAND_METRIC, period) == ("demand_energy", "SUM")


def test_price_stays_on_avg() -> None:
    assert get_value_expression(PRICE_METRIC, MilestonePeriod.interval) == ("price", "AVG")


def test_incremental_network_demand_query_sums_regions() -> None:
    query = build_period_aggregation_query(
        metric_def=DEMAND_METRIC,
        network=NetworkNEM,
        grouping=GROUPING_NETWORK,
        period=MilestonePeriod.interval,
        period_start=datetime(2026, 9, 20, 3, 0),
        period_end=datetime(2026, 9, 20, 3, 5),
    )

    assert "SUM(demand) as value" in query
    assert "AVG(demand)" not in query
    # the network grouping has no region key — this is why AVG averaged the five regional rows
    assert "network_region" not in query.split("GROUP BY")[1]


def test_incremental_region_demand_query_sums_the_single_row() -> None:
    """One row per (interval, network_region) — SUM and AVG agree, SUM is the consistent choice."""
    query = build_period_aggregation_query(
        metric_def=DEMAND_METRIC,
        network=NetworkNEM,
        grouping=GROUPING_REGION,
        period=MilestonePeriod.interval,
        period_start=datetime(2026, 9, 20, 3, 0),
        period_end=datetime(2026, 9, 20, 3, 5),
    )

    assert "SUM(demand) as value" in query
    assert "network_region" in query.split("GROUP BY")[1]


def test_incremental_price_query_still_averages() -> None:
    query = build_period_aggregation_query(
        metric_def=PRICE_METRIC,
        network=NetworkNEM,
        grouping=GROUPING_NETWORK,
        period=MilestonePeriod.interval,
        period_start=datetime(2026, 9, 20, 3, 0),
        period_end=datetime(2026, 9, 20, 3, 5),
    )

    assert "AVG(price) as value" in query


def test_backlog_interval_demand_query_sums_regions() -> None:
    query = _backlog_query(MilestoneType.demand, MilestonePeriod.interval)

    assert "SUM(demand)" in query
    assert "AVG(demand)" not in query


def test_backlog_day_demand_query_sums_energy() -> None:
    query = _backlog_query(MilestoneType.demand, MilestonePeriod.day)

    assert "SUM(demand_energy)" in query


def test_backlog_price_query_still_averages() -> None:
    query = _backlog_query(MilestoneType.price, MilestonePeriod.interval)

    assert "AVG(price)" in query
