"""Regression guard for #662: the backlog holds rooftop rows back to the last settled interval.

`run_milestone_analysis` — behind the full rebuild, the gap backfill, the monthly reconciliation
and `run_update_milestone_analysis_to_now` — ran every interval series to the last completed
interval, so the tail of any series with rooftop in it was summed on grid-only generation. That
is how the false VIC1 generation interval lows got in (#652), and a rebuild would mint them again.

At the interval period, rows that can contain rooftop now stop at the last settled interval, per
row and inside `base_stats` so the running extremes never see the partial rows (#654/#656). The
SQL is built from the same definition as the incremental path's `row_contains_rooftop`.
"""

from datetime import datetime, timedelta

import pytest

from opennem.recordreactor import backlog
from opennem.recordreactor.backlog import GroupingConfig, _analyze_milestone_records
from opennem.recordreactor.metric_registry import (
    GENERATION_GROUPINGS,
    MARKET_GROUPINGS,
    get_metric_registry,
    get_rooftop_settled_sql,
    row_contains_rooftop,
)
from opennem.recordreactor.schema import MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM, NetworkWEM

END = datetime(2026, 9, 22, 14, 0)
SETTLED = datetime(2026, 9, 22, 12, 15)
SETTLED_LITERAL = "toDateTime('2026-09-22 12:15:00')"

GROUPING_NETWORK = GroupingConfig(name="network", group_by_fields=[])
GROUPING_REGION = GroupingConfig(name="region", group_by_fields=["network_region"])
GROUPING_FUELTECH = GroupingConfig(name="fueltech", group_by_fields=["fueltech_group_id"])
GROUPING_RENEWABLE = GroupingConfig(name="renewable", group_by_fields=["renewable"])
GROUPING_REGION_FUELTECH = GroupingConfig(name="region_fueltech", group_by_fields=["network_region", "fueltech_group_id"])
GROUPING_REGION_RENEWABLE = GroupingConfig(name="region_renewable", group_by_fields=["network_region", "renewable"])


class _QueryCapturingClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list:
        self.queries.append(query)
        return []


def _base_stats(
    milestone_type: MilestoneType,
    grouping: GroupingConfig,
    period: MilestonePeriod = MilestonePeriod.interval,
    settled: datetime | None = SETTLED,
) -> str:
    client = _QueryCapturingClient()
    _analyze_milestone_records(
        client=client,  # type: ignore[arg-type]
        network=NetworkNEM,
        period=period,
        milestone_type=milestone_type,
        grouping=grouping,
        start_date=datetime(2026, 9, 1),
        end_date=END,
        settled_interval=settled,
    )
    query = client.queries[0]
    return query[query.index("WITH base_stats AS (") : query.index("running_maxes AS (")]


@pytest.mark.parametrize(
    "milestone_type,grouping",
    [
        (MilestoneType.power, GROUPING_NETWORK),
        (MilestoneType.power, GROUPING_REGION),
        (MilestoneType.proportion, GROUPING_NETWORK),
        (MilestoneType.proportion, GROUPING_REGION),
    ],
)
def test_totals_and_proportion_end_at_settled(milestone_type, grouping) -> None:
    """Every row carries rooftop: the whole query stops at the settled interval."""
    body = _base_stats(milestone_type, grouping)

    assert f"and interval <= {SETTLED_LITERAL}" in body


@pytest.mark.parametrize("grouping", [GROUPING_FUELTECH, GROUPING_REGION_FUELTECH])
def test_fueltech_grouping_holds_back_only_solar(grouping) -> None:
    body = _base_stats(MilestoneType.power, grouping)

    assert f"NOT (fueltech_group_id = 'solar' AND interval > {SETTLED_LITERAL})" in body
    assert f"interval <= {SETTLED_LITERAL}" not in body


@pytest.mark.parametrize("grouping", [GROUPING_RENEWABLE, GROUPING_REGION_RENEWABLE])
def test_renewable_grouping_holds_back_only_renewables(grouping) -> None:
    body = _base_stats(MilestoneType.power, grouping)

    assert f"NOT (renewable = 1 AND interval > {SETTLED_LITERAL})" in body
    assert f"interval <= {SETTLED_LITERAL}" not in body


@pytest.mark.parametrize(
    "milestone_type,grouping",
    [(MilestoneType.demand, GROUPING_NETWORK), (MilestoneType.demand, GROUPING_REGION), (MilestoneType.price, GROUPING_REGION)],
)
def test_demand_and_price_are_not_held_back(milestone_type, grouping) -> None:
    assert SETTLED_LITERAL not in _base_stats(milestone_type, grouping)


@pytest.mark.parametrize(
    "milestone_type,grouping",
    [
        (MilestoneType.energy, GROUPING_NETWORK),
        (MilestoneType.energy, GROUPING_FUELTECH),
        (MilestoneType.energy, GROUPING_RENEWABLE),
        (MilestoneType.proportion, GROUPING_REGION),
    ],
)
def test_day_period_keeps_its_bucket_trim(milestone_type, grouping) -> None:
    """Day+ trims to the last complete bucket and is never capped at the settled interval."""
    body = _base_stats(milestone_type, grouping, period=MilestonePeriod.day)

    assert SETTLED_LITERAL not in body
    assert "interval < toStartOfDay(toDateTime('2026-09-22 14:00:00'))" in body


def test_no_settled_interval_applies_no_cap() -> None:
    assert "<= toDateTime" not in _base_stats(MilestoneType.power, GROUPING_NETWORK, settled=None)


# --- helper agrees with row_contains_rooftop -------------------------------------------------

_SAMPLE_ROWS = [
    {},
    {"network_region": "VIC1"},
    {"fueltech_group_id": "solar"},
    {"fueltech_group_id": "coal"},
    {"fueltech_group_id": "wind"},
    {"network_region": "SA1", "fueltech_group_id": "solar"},
    {"network_region": "QLD1", "fueltech_group_id": "coal"},
    {"renewable": 1},
    {"renewable": 0},
    {"network_region": "QLD1", "renewable": 1},
    {"network_region": "QLD1", "renewable": 0},
]


def _sql_holds_back(sql: str, row: dict) -> bool:
    """Evaluate the helper's clause for a row at an interval after the settled one."""
    if not sql:
        return False
    if sql.startswith("and interval <= "):
        return True
    for column, literal in (("fueltech_group_id", "'solar'"), ("renewable", "1")):
        if f"NOT ({column} = {literal} AND" in sql:
            expected = "solar" if column == "fueltech_group_id" else 1
            return row.get(column) == expected
    raise AssertionError(f"unrecognised clause: {sql}")


@pytest.mark.parametrize("metric_def", get_metric_registry(), ids=lambda m: m.metric.value)
def test_sql_helper_agrees_with_row_contains_rooftop(metric_def) -> None:
    """The backlog's SQL gate and the incremental path's per-row gate must hold back the same rows."""
    for grouping in [*GENERATION_GROUPINGS, *MARKET_GROUPINGS]:
        sql = get_rooftop_settled_sql(metric_def.metric, grouping.group_by_fields, "interval", SETTLED)

        for row in _SAMPLE_ROWS:
            if not set(row) <= set(grouping.group_by_fields):
                continue
            assert _sql_holds_back(sql, row) == row_contains_rooftop(metric_def, grouping, row), (
                metric_def.metric,
                grouping.name,
                row,
            )


# --- run_milestone_analysis wiring -----------------------------------------------------------


@pytest.mark.asyncio
async def test_settled_interval_is_computed_once_per_network_and_passed_to_interval_queries(monkeypatch) -> None:
    settled_calls: list[tuple[str, datetime]] = []
    analysed: list[tuple[str, MilestonePeriod, datetime | None]] = []

    def _settled(client, network, now):
        settled_calls.append((network.code, now))
        return now - timedelta(minutes=90)

    def _analyse(**kwargs):
        analysed.append((kwargs["network"].code, kwargs["period"], kwargs["settled_interval"]))
        return []

    async def _persist(records):
        return []

    monkeypatch.setattr(backlog, "get_clickhouse_client", lambda: object())
    monkeypatch.setattr(backlog, "get_last_settled_interval", _settled)
    monkeypatch.setattr(backlog, "_analyze_milestone_records", _analyse)
    monkeypatch.setattr(backlog, "check_and_persist_milestones_chunked", _persist)

    await backlog.run_milestone_analysis(start_date=datetime(2026, 9, 21), end_date=END, networks=[NetworkNEM, NetworkWEM])

    # one rooftop query per network, anchored on the last interval the run can see
    last_visible = END - timedelta(minutes=5)
    assert sorted(settled_calls) == [("NEM", last_visible), ("WEM", last_visible)]

    for code, period, settled in analysed:
        if period == MilestonePeriod.interval:
            assert settled == last_visible - timedelta(minutes=90), code
        else:
            assert settled is None, (code, period)
