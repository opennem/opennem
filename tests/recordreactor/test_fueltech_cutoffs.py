"""Regression guard for #656: fueltech date cutoffs belong in the query, not after it.

The backlog computed its running extremes over all history and then dropped the pre-cutoff records
in `_analyzed_record_to_milestone_schema`. Solar and wind only grow, so every low they produce sits
at the start of their history and every one was discarded — the chains were written to the table
empty, and the live checker minted the next value it saw as an all-time record.

Measured on dev ClickHouse for `au.wem.solar.energy.day.low`: the old query yields 4 low records
between 2015-03-21 and 2015-05-16 (minimum 180.4 MWh), all before the 2015-10-26 solar cutoff and
therefore all discarded. With the cutoff in the WHERE it yields 7 records from 2015-10-26 down to
773.8 MWh on 2020-05-24, all of which survive.
"""

from datetime import datetime

import pytest

from opennem.recordreactor.backlog import GroupingConfig, _analyze_milestone_records
from opennem.recordreactor.metric_registry import get_fueltech_cutoff_sql, get_fueltech_date_cutoffs
from opennem.recordreactor.schema import MilestoneFueltechGrouping, MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM

GROUPING_NETWORK = GroupingConfig(name="network", group_by_fields=[])
GROUPING_REGION = GroupingConfig(name="region", group_by_fields=["network_region"])
GROUPING_FUELTECH = GroupingConfig(name="fueltech", group_by_fields=["fueltech_group_id"])
GROUPING_REGION_FUELTECH = GroupingConfig(name="region_fueltech", group_by_fields=["network_region", "fueltech_group_id"])
GROUPING_RENEWABLE = GroupingConfig(name="renewable", group_by_fields=["renewable"])


class _QueryCapturingClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list:
        self.queries.append(query)
        return []


def _captured_query(grouping: GroupingConfig, milestone_type: MilestoneType = MilestoneType.energy) -> str:
    client = _QueryCapturingClient()
    _analyze_milestone_records(
        client=client,  # type: ignore[arg-type]
        network=NetworkNEM,
        period=MilestonePeriod.day,
        milestone_type=milestone_type,
        grouping=grouping,
        start_date=None,
        end_date=datetime(2026, 9, 22),
    )
    assert len(client.queries) == 1
    return client.queries[0]


def _base_stats_body(query: str) -> str:
    """The CTE the running max/min windows are computed over."""
    return query[query.index("WITH base_stats AS (") : query.index("running_maxes AS (")]


@pytest.mark.parametrize("fueltech,cutoff", sorted(get_fueltech_date_cutoffs().items()))
def test_cutoff_dates_come_from_the_registry(fueltech: str, cutoff: datetime) -> None:
    """One source of truth — the backlog used to carry its own hardcoded copy."""
    if fueltech in (MilestoneFueltechGrouping.renewables.value, MilestoneFueltechGrouping.fossils.value):
        sql = get_fueltech_cutoff_sql(["renewable"], "time_bucket")
        assert "renewable = 1" in sql
    else:
        sql = get_fueltech_cutoff_sql(["fueltech_group_id"], "time_bucket")
        assert f"fueltech_group_id = '{fueltech}'" in sql

    assert cutoff.strftime("%Y-%m-%d %H:%M:%S") in sql


def test_no_cutoff_for_groupings_without_a_fueltech_key() -> None:
    """A network or region total has no single fueltech to cut off."""
    assert get_fueltech_cutoff_sql([], "time_bucket") == ""
    assert get_fueltech_cutoff_sql(["network_region"], "time_bucket") == ""
    assert get_fueltech_cutoff_sql(None, "time_bucket") == ""


def test_cutoff_is_inside_base_stats() -> None:
    """In the WHERE, so the running extremes are computed over post-cutoff data only."""
    body = _base_stats_body(_captured_query(GROUPING_FUELTECH))

    assert "fueltech_group_id = 'solar'" in body
    assert "toDateTime('2015-10-26 00:00:00')" in body
    assert "fueltech_group_id = 'wind'" in body
    assert "toDateTime('2009-07-01 00:00:00')" in body


def test_cutoff_applies_to_the_region_fueltech_grouping() -> None:
    body = _base_stats_body(_captured_query(GROUPING_REGION_FUELTECH))

    assert "fueltech_group_id = 'solar'" in body


def test_renewable_grouping_cuts_off_the_renewables_rows_only() -> None:
    body = _base_stats_body(_captured_query(GROUPING_RENEWABLE))

    assert "renewable = 1" in body
    # fossils has no cutoff
    assert "renewable = 0" not in body


def test_network_and_region_totals_are_not_cut_off() -> None:
    """Behaviour unchanged for these: the post-query filter never touched them either."""
    for grouping in (GROUPING_NETWORK, GROUPING_REGION):
        body = _base_stats_body(_captured_query(grouping))
        assert "fueltech_group_id =" not in body
        assert "renewable = 1" not in body


def test_metric_wide_date_cutoffs_are_untouched() -> None:
    """The existing per-metric floors stay exactly where they were."""
    energy = _base_stats_body(_captured_query(GROUPING_FUELTECH))
    demand = _base_stats_body(_captured_query(GROUPING_NETWORK, milestone_type=MilestoneType.demand))

    assert "time_bucket >= toDateTime('2000-01-01')" in energy
    assert "time_bucket >= toDateTime('2009-07-01')" in demand
