"""Regression guard for #654: a bounded run must not mint a record at its own window edge.

`start_date` was applied inside `base_stats`, so the running max/min windows restarted at the edge
of the window and the first row always had `prev_max`/`prev_min` NULL — emitted as a record purely
because the window started there. With no prior chain to compare against those false records
persisted, and the incremental worker ratcheted them ever since
(`au.nem.wind.energy.day.low` = 70,337 MWh with 5,069 lower days in history).

`start_date` now filters the OUTPUT rows and the running extremes are seeded from all prior data.
`end_date` semantics and the `date_cutoffs` are unchanged.

Verified against dev ClickHouse: demand/day/network bounded to 2026-09-06..2026-09-20 emitted a
false high AND low at 2026-09-06 plus a six-row ratchet before this change, and nothing after it.
"""

from datetime import datetime

from opennem.recordreactor.backlog import GroupingConfig, _analyze_milestone_records
from opennem.recordreactor.schema import MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM

GROUPING_NETWORK = GroupingConfig(name="network", group_by_fields=[])
GROUPING_FUELTECH = GroupingConfig(name="fueltech", group_by_fields=["fueltech_group_id"])

WINDOW_START = datetime(2026, 9, 6)
WINDOW_END = datetime(2026, 9, 20)
START_LITERAL = "toDateTime('2026-09-06 00:00:00')"


class _QueryCapturingClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list:
        self.queries.append(query)
        return []


def _captured_query(
    milestone_type: MilestoneType = MilestoneType.energy,
    period: MilestonePeriod = MilestonePeriod.day,
    grouping: GroupingConfig = GROUPING_NETWORK,
    start_date: datetime | None = WINDOW_START,
) -> str:
    client = _QueryCapturingClient()
    _analyze_milestone_records(
        client=client,  # type: ignore[arg-type]
        network=NetworkNEM,
        period=period,
        milestone_type=milestone_type,
        grouping=grouping,
        start_date=start_date,
        end_date=WINDOW_END,
    )
    assert len(client.queries) == 1
    return client.queries[0]


def _base_stats_body(query: str) -> str:
    """The base_stats CTE — the rows the running max/min windows are computed over."""
    start = query.index("WITH base_stats AS (")
    end = query.index("running_maxes AS (")
    return query[start:end]


def test_window_start_does_not_limit_the_running_extremes() -> None:
    """The seed data for running_max/running_min must span everything before the window."""
    query = _captured_query()

    assert START_LITERAL not in _base_stats_body(query)


def test_window_start_filters_the_output_rows() -> None:
    """Buckets before the window are still scanned, they just aren't emitted as records."""
    query = _captured_query()

    assert query.rstrip().endswith("ORDER BY interval")
    # the filter sits after the union subquery closes, not inside it
    outer = query.rstrip().removesuffix("ORDER BY interval").rsplit("\n    )\n", 1)[-1]
    assert f"WHERE interval >= {START_LITERAL}" in outer


def test_window_start_applies_to_every_grouping() -> None:
    query = _captured_query(grouping=GROUPING_FUELTECH)

    assert START_LITERAL not in _base_stats_body(query)
    assert f"WHERE interval >= {START_LITERAL}" in query


def test_interval_period_window_is_also_output_filtered() -> None:
    query = _captured_query(milestone_type=MilestoneType.power, period=MilestonePeriod.interval)

    assert START_LITERAL not in _base_stats_body(query)
    assert f"WHERE interval >= {START_LITERAL}" in query


def test_end_date_still_trims_inside_base_stats() -> None:
    """end_date semantics are unchanged: it trims the source rows to the last complete period."""
    query = _captured_query()

    assert "toStartOfDay(toDateTime('2026-09-20 00:00:00'))" in _base_stats_body(query)


def test_date_cutoffs_stay_inside_base_stats() -> None:
    """The metric date cutoffs are a data-quality floor, not a window — they stay where they are."""
    energy_query = _captured_query()
    demand_query = _captured_query(milestone_type=MilestoneType.demand)

    assert "time_bucket >= toDateTime('2000-01-01')" in _base_stats_body(energy_query)
    assert "time_bucket >= toDateTime('2009-07-01')" in _base_stats_body(demand_query)


def test_unbounded_run_has_no_output_filter() -> None:
    """A full rebuild passes no start_date and must emit every record it finds."""
    query = _captured_query(start_date=None)

    assert "WHERE interval >=" not in query
    assert query.rstrip().endswith("ORDER BY interval")
