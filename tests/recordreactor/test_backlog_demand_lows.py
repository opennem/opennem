"""Regression guard for #640: the backlog must emit demand low records at day+ periods.

`_analyze_milestone_records` hardcoded `interval_count = "1"` for demand, so every low candidate
failed the `interval_count >= threshold` guard (288 for day) inside the running_mins CTE and the
full-history rebuild silently produced zero demand low records. The #605 repair then purged the
series, left every `.low` chain empty, and the incremental worker minted false record lows into
the void through August 2026.

These tests capture the generated ClickHouse SQL via a stub client and assert the interval count
is real at day+ (and only ever 1 at the interval period, where each row IS a single interval).
"""

from datetime import datetime

from opennem.recordreactor.backlog import GroupingConfig, _analyze_milestone_records
from opennem.recordreactor.schema import MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM

GROUPING_NETWORK = GroupingConfig(name="network", group_by_fields=[])


class _QueryCapturingClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list:
        self.queries.append(query)
        return []


def _captured_query(period: MilestonePeriod) -> str:
    client = _QueryCapturingClient()
    records = _analyze_milestone_records(
        client=client,  # type: ignore[arg-type]
        network=NetworkNEM,
        period=period,
        milestone_type=MilestoneType.demand,
        grouping=GROUPING_NETWORK,
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2026, 1, 1),
    )
    assert records == []
    assert len(client.queries) == 1
    return client.queries[0]


def test_demand_day_uses_real_interval_count() -> None:
    query = _captured_query(MilestonePeriod.day)
    assert "count(distinct interval) as interval_count" in query
    assert "1 as interval_count" not in query
    # the low-record completeness guard must be able to pass on a full day
    assert "interval_count >= 288" in query


def test_demand_month_uses_real_interval_count() -> None:
    query = _captured_query(MilestonePeriod.month)
    assert "count(distinct interval) as interval_count" in query
    assert "interval_count >= 8000" in query


def test_demand_interval_period_keeps_count_of_one() -> None:
    query = _captured_query(MilestonePeriod.interval)
    assert "1 as interval_count" in query
    assert "count(distinct interval) as interval_count" not in query
