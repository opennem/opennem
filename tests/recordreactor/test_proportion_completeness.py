"""Regression guard for #662: renewable proportion records only come from complete data.

market_summary leaves demand_gross and generation_renewable NULL for a region and interval when
any input is missing (#661). sum() skips NULLs, so a NEM proportion over four of five regions, or
a day with an interval missing, came out as a plausible partial number. The rule is now NULL
unless every input is present: every region for an interval, every interval for a day+ bucket.
Day+ used to wave every bucket through the low guard with `interval_count = 10000000000`.

The SQL checks run anywhere. The data checks execute the generated queries in `clickhouse local`
against an in-memory fixture, and are skipped where the binary isn't installed.
"""

import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta

import pytest

from opennem.recordreactor.backlog import GroupingConfig as BacklogGroupingConfig
from opennem.recordreactor.backlog import _analyze_milestone_records
from opennem.recordreactor.metric_registry import (
    GROUPING_NETWORK,
    GROUPING_REGION,
    PROPORTION_CLAMPED_SQL,
    GroupingConfig,
    get_metric_registry,
    get_proportion_sql,
)
from opennem.recordreactor.queries_incremental import build_period_aggregation_query
from opennem.recordreactor.schema import MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM, NetworkWEM

PROPORTION = next(m for m in get_metric_registry() if m.metric == MilestoneType.proportion)
REGIONS = NetworkNEM.regions or []


class _QueryCapturingClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list:
        self.queries.append(query)
        return []


def _backlog_query(
    grouping: GroupingConfig,
    period: MilestonePeriod,
    end_date: datetime,
    network=NetworkNEM,
) -> str:
    client = _QueryCapturingClient()
    _analyze_milestone_records(
        client=client,  # type: ignore[arg-type]
        network=network,
        period=period,
        milestone_type=MilestoneType.proportion,
        grouping=BacklogGroupingConfig(name=grouping.name, group_by_fields=list(grouping.group_by_fields)),
        start_date=datetime(2026, 9, 1),
        end_date=end_date,
    )
    return client.queries[0]


def _incremental_query(
    grouping: GroupingConfig, period: MilestonePeriod, start: datetime, end: datetime, network=NetworkNEM
) -> str:
    return build_period_aggregation_query(PROPORTION, network, grouping, period, start, end)


# --- SQL shape -------------------------------------------------------------------------------


def test_day_hack_is_gone() -> None:
    assert "10000000000" not in _backlog_query(GROUPING_NETWORK, MilestonePeriod.day, datetime(2026, 9, 20))


@pytest.mark.parametrize("period", [MilestonePeriod.interval, MilestonePeriod.day, MilestonePeriod.month])
@pytest.mark.parametrize("grouping", [GROUPING_NETWORK, GROUPING_REGION])
def test_both_paths_use_the_same_guard(grouping, period) -> None:
    """The backlog and the incremental query embed the one completeness expression."""
    backlog = _backlog_query(grouping, period, datetime(2026, 9, 20))
    incremental = _incremental_query(grouping, period, datetime(2026, 9, 1), datetime(2026, 9, 20))

    backlog_value, _ = get_proportion_sql(
        NetworkNEM,
        grouping.group_by_fields,
        period,
        "interval",
        "market_summary.interval"
        if period == MilestonePeriod.interval
        else f"toStartOf{period.value.title()}(market_summary.interval)",
    )
    incremental_value, _ = get_proportion_sql(
        NetworkNEM,
        grouping.group_by_fields,
        period,
        "interval",
        "interval" if period == MilestonePeriod.interval else f"toStartOf{period.value.title()}(interval)",
    )

    assert backlog_value in backlog
    assert incremental_value in incremental
    # the guard is the same modulo the table qualifier on the bucket expression
    assert backlog_value.replace("market_summary.", "") == incremental_value
    # and still wraps the 200% clamp
    assert PROPORTION_CLAMPED_SQL in backlog_value


def test_network_interval_requires_every_region() -> None:
    value, count = get_proportion_sql(NetworkNEM, [], MilestonePeriod.interval, "interval", "interval")

    assert f"= 1 * {len(REGIONS)}" in value
    assert count == "1"


def test_region_interval_requires_its_own_row() -> None:
    value, _ = get_proportion_sql(NetworkNEM, ["network_region"], MilestonePeriod.interval, "interval", "interval")

    assert "= 1 * 1" in value


def test_wem_requires_its_one_region() -> None:
    value, _ = get_proportion_sql(NetworkWEM, [], MilestonePeriod.interval, "interval", "interval")

    assert "network_region IN ('WEM')" in value
    assert "= 1 * 1" in value


def test_wem_day_buckets_before_the_five_minute_cutover_are_exempt() -> None:
    """WEM was 30-minute before WEMDE; the schema's 5-minute size can't count those buckets."""
    value, count = get_proportion_sql(NetworkWEM, [], MilestonePeriod.day, "interval", "toStartOfDay(interval)")

    assert "toStartOfDay(interval) < toDateTime('2023-10-01 08:00:00') OR" in value
    assert count.startswith("if(toStartOfDay(interval) < toDateTime('2023-10-01 08:00:00')")


def test_nem_day_buckets_have_no_exemption() -> None:
    value, _ = get_proportion_sql(NetworkNEM, [], MilestonePeriod.day, "interval", "toStartOfDay(interval)")

    assert "2023-10-01" not in value


# --- executed against clickhouse local -------------------------------------------------------

_CLICKHOUSE = shutil.which("clickhouse")
requires_clickhouse = pytest.mark.skipif(_CLICKHOUSE is None, reason="clickhouse local binary not installed")

_COLUMNS = (
    "interval DateTime64(3), network_id String, network_region String, "
    "demand_gross Nullable(Float64), generation_renewable Nullable(Float64)"
)


def _fixture_rows(start: datetime, intervals: int, missing: set[tuple[datetime, str]]) -> list[str]:
    rows: list[str] = []
    for i in range(intervals):
        interval = start + timedelta(minutes=5 * i)
        for region in REGIONS:
            ts = interval.strftime("%Y-%m-%d %H:%M:%S")
            if (interval, region) in missing:
                rows.append(f"('{ts}','NEM','{region}',NULL,NULL)")
            else:
                rows.append(f"('{ts}','NEM','{region}',1000,500)")
    return rows


def _run(query: str, rows: list[str]) -> list[dict]:
    """Run a generated query in clickhouse local over the fixture instead of the real table."""
    source = f"(SELECT * FROM values('{_COLUMNS}', {', '.join(rows)})) AS market_summary"
    query = query.replace("market_summary FINAL", source)
    # clickhouse local 24.1 has no generateUUIDv7; the uuid is irrelevant here
    query = query.replace("generateUUIDv7()", "generateUUIDv4()")
    result = subprocess.run(
        [_CLICKHOUSE or "clickhouse", "local", "--output_format_json_quote_64bit_integers=0"],
        input=f"{query} FORMAT JSONEachRow",
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def _base_stats_only(query: str) -> str:
    """The backlog's base_stats CTE on its own — the values the running extremes are computed over."""
    body = query[: query.index("running_maxes AS (")].rstrip().rstrip(",")
    return f"{body}\nSELECT * FROM base_stats"


def _bucket(ts: str) -> datetime:
    return datetime.fromisoformat(re.sub(r"\.\d+$", "", ts))


INTERVAL_START = datetime(2026, 9, 20, 12, 0)
INCOMPLETE_INTERVAL = INTERVAL_START + timedelta(minutes=5)
INTERVAL_ROWS_MISSING = {(INCOMPLETE_INTERVAL, "VIC1")}


@requires_clickhouse
def test_nem_interval_with_one_region_null_has_no_value() -> None:
    rows = _fixture_rows(INTERVAL_START, 2, INTERVAL_ROWS_MISSING)
    query = _incremental_query(GROUPING_NETWORK, MilestonePeriod.interval, INTERVAL_START, INTERVAL_START + timedelta(minutes=10))

    values = {_bucket(r["time_bucket"]): r["value"] for r in _run(query, rows)}

    # complete: 5 x 500 / 5 x 1000
    assert values[INTERVAL_START] == 50.0
    # four of five regions must not produce a partial NEM proportion
    assert values[INCOMPLETE_INTERVAL] is None


@requires_clickhouse
def test_region_interval_null_only_for_the_missing_region() -> None:
    rows = _fixture_rows(INTERVAL_START, 2, INTERVAL_ROWS_MISSING)
    query = _incremental_query(GROUPING_REGION, MilestonePeriod.interval, INTERVAL_START, INTERVAL_START + timedelta(minutes=10))

    values = {(_bucket(r["time_bucket"]), r["network_region"]): r["value"] for r in _run(query, rows)}

    assert values[(INCOMPLETE_INTERVAL, "VIC1")] is None
    assert values[(INCOMPLETE_INTERVAL, "NSW1")] == 50.0


DAY_COMPLETE = datetime(2026, 9, 18)
DAY_INCOMPLETE = datetime(2026, 9, 19)
DAY_ROWS_MISSING = {(DAY_INCOMPLETE + timedelta(hours=13, minutes=5), "SA1")}


@requires_clickhouse
def test_day_with_one_incomplete_interval_is_excluded() -> None:
    rows = _fixture_rows(DAY_COMPLETE, 288 * 2, DAY_ROWS_MISSING)
    query = _incremental_query(GROUPING_NETWORK, MilestonePeriod.day, DAY_COMPLETE, DAY_INCOMPLETE + timedelta(days=1))

    by_day = {_bucket(r["time_bucket"]): r for r in _run(query, rows)}

    assert by_day[DAY_COMPLETE]["value"] == 50.0
    assert by_day[DAY_COMPLETE]["interval_count"] == 288
    assert by_day[DAY_INCOMPLETE]["value"] is None
    assert by_day[DAY_INCOMPLETE]["interval_count"] == 287


@requires_clickhouse
def test_backlog_emits_no_record_for_the_incomplete_day() -> None:
    """Neither a high nor a low: the old hack let any partial day through as a low candidate."""
    rows = _fixture_rows(DAY_COMPLETE, 288 * 2, DAY_ROWS_MISSING)
    query = _backlog_query(GROUPING_NETWORK, MilestonePeriod.day, DAY_INCOMPLETE + timedelta(days=1))

    records = _run(query, rows)

    assert {_bucket(r["interval"]) for r in records} == {DAY_COMPLETE}


@requires_clickhouse
@pytest.mark.parametrize(
    "grouping,period,start,intervals,missing,end",
    [
        (
            GROUPING_NETWORK,
            MilestonePeriod.interval,
            INTERVAL_START,
            2,
            INTERVAL_ROWS_MISSING,
            INTERVAL_START + timedelta(minutes=10),
        ),
        (
            GROUPING_REGION,
            MilestonePeriod.interval,
            INTERVAL_START,
            2,
            INTERVAL_ROWS_MISSING,
            INTERVAL_START + timedelta(minutes=10),
        ),
        (GROUPING_NETWORK, MilestonePeriod.day, DAY_COMPLETE, 288 * 2, DAY_ROWS_MISSING, DAY_INCOMPLETE + timedelta(days=1)),
        (GROUPING_REGION, MilestonePeriod.day, DAY_COMPLETE, 288 * 2, DAY_ROWS_MISSING, DAY_INCOMPLETE + timedelta(days=1)),
    ],
)
def test_backlog_and_incremental_agree(grouping, period, start, intervals, missing, end) -> None:
    rows = _fixture_rows(start, intervals, missing)

    incremental = _run(_incremental_query(grouping, period, start, end), rows)
    backlog = _run(_base_stats_only(_backlog_query(grouping, period, end)), rows)

    def _key(row: dict) -> tuple:
        return (_bucket(row["time_bucket"]), row.get("network_region"))

    assert {_key(r): (r["value"], r["interval_count"]) for r in incremental} == {
        _key(r): (r["total_value"], r["interval_count"]) for r in backlog
    }
