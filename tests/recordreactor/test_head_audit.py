"""#786: milestone chain head audit.

Pure comparison logic first (no database), then one end-to-end run of `audit_heads` against a fake
ClickHouse client that answers the daily-series, interval-count and point queries from canned rows.
The cases are the five false heads found in the 2026-11-02 validation.
"""

import random
import threading
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import pytest

from opennem.recordreactor.head_audit import (
    AuditStatus,
    BucketValue,
    ChainHead,
    HeadFinding,
    Tolerances,
    attach_interval_counts,
    audit_heads,
    bucket_end,
    bucket_start,
    clamp_proportion,
    evaluate_interval_head,
    evaluate_period_head,
    filter_since,
    head_audit_reminder,
    head_spec,
    rollup_proportion,
    rollup_series,
    rollup_sum,
    select_heads,
    series_cutoff,
)
from opennem.recordreactor.schema import MilestoneAggregate, MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM, NetworkWEM

HIGH = MilestoneAggregate.high
LOW = MilestoneAggregate.low


def _head(
    record_id: str,
    interval: datetime,
    value: float,
    *,
    metric: str = "energy",
    period: str = "month",
    aggregate: MilestoneAggregate = HIGH,
    network_id: str = "NEM",
    network_region: str | None = None,
    fueltech_id: str | None = None,
    significance: int = 8,
    prev_interval: datetime | None = None,
    prev_value: float | None = None,
) -> ChainHead:
    return ChainHead(
        record_id=record_id,
        interval=interval,
        aggregate=aggregate,
        metric=metric,
        period=period,
        significance=significance,
        value=value,
        network_id=network_id,
        network_region=network_region,
        fueltech_id=fueltech_id,
        prev_interval=prev_interval,
        prev_value=prev_value,
    )


def _months(values: dict[str, float], interval_count: int = 8928) -> dict[datetime, BucketValue]:
    return {datetime.fromisoformat(k): BucketValue(value=v, interval_count=interval_count) for k, v in values.items()}


# --- head -> series mapping --------------------------------------------------------------------


def test_head_spec_region_fueltech() -> None:
    spec = head_spec(
        _head(
            "au.nem.vic1.battery_discharging.energy.month.high",
            datetime(2026, 10, 1),
            1,
            network_region="VIC1",
            fueltech_id="battery_discharging",
        )
    )
    assert spec is not None
    assert spec.network == NetworkNEM
    assert spec.metric == MilestoneType.energy
    assert spec.grouping.group_by_fields == ["network_region", "fueltech_group_id"]
    assert spec.key == ("VIC1", "battery_discharging")


def test_head_spec_demand_chain_maps_to_demand_metric() -> None:
    spec = head_spec(_head("au.nem.demand.energy.day.high", datetime(2026, 7, 1), 1, period="day", fueltech_id="demand"))
    assert spec is not None
    assert spec.metric == MilestoneType.demand
    assert spec.grouping.group_by_fields == []
    assert spec.key == ()


def test_head_spec_renewables_and_fossils_use_renewable_flag() -> None:
    ren = head_spec(
        _head(
            "au.wem.renewables.power.interval.high",
            datetime(2026, 10, 28, 11, 40),
            1,
            metric="power",
            period="interval",
            network_id="WEM",
            fueltech_id="renewables",
        )
    )
    fos = head_spec(_head("au.nem.fossils.energy.day.low", datetime(2026, 7, 1), 1, period="day", fueltech_id="fossils"))
    assert ren is not None and ren.network == NetworkWEM and ren.key == (True,)
    assert fos is not None and fos.key == (False,)
    assert ren.grouping.group_by_fields == ["renewable"]


def test_head_spec_proportion_and_unsupported() -> None:
    spec = head_spec(_head("au.nem.renewables.proportion.month.high", datetime(2026, 9, 1), 70, metric="renewable_proportion"))
    assert spec is not None and spec.metric == MilestoneType.proportion and spec.key == ()
    assert head_spec(_head("x", datetime(2026, 9, 1), 1, period="week")) is None
    assert head_spec(_head("x", datetime(2026, 9, 1), 1, network_id="NEMDE")) is None
    assert head_spec(_head("x", datetime(2026, 9, 1), 1, metric="power", period="day")) is None


# --- buckets, cutoffs, rollups ------------------------------------------------------------------


def test_buckets() -> None:
    assert bucket_start(date(2026, 8, 17), MilestonePeriod.quarter) == datetime(2026, 7, 1)
    assert bucket_start(datetime(2026, 8, 17, 13, 5), MilestonePeriod.month) == datetime(2026, 8, 1)
    assert bucket_end(datetime(2026, 10, 1), MilestonePeriod.quarter) == datetime(2027, 1, 1)
    assert bucket_end(datetime(2024, 2, 1), MilestonePeriod.month) == datetime(2024, 3, 1)
    assert bucket_end(datetime(2024, 1, 1), MilestonePeriod.year) == datetime(2025, 1, 1)


def test_series_cutoff_uses_metric_and_fueltech_cutoffs() -> None:
    assert series_cutoff(MilestoneType.energy, [], ()) == datetime(2000, 1, 1)
    assert series_cutoff(MilestoneType.demand, ["network_region"], ("NSW1",)) == datetime(2009, 7, 1)
    assert series_cutoff(MilestoneType.energy, ["fueltech_group_id"], ("solar",)) == datetime(2015, 10, 26)
    assert series_cutoff(MilestoneType.energy, ["fueltech_group_id"], ("coal",)) == datetime(2000, 1, 1)


def test_rollup_sum_sums_values_and_interval_counts() -> None:
    rows = [
        (date(2026, 7, 30), ("VIC1",), 10.0, 288),
        (date(2026, 7, 31), ("VIC1",), 20.0, 288),
        (date(2026, 8, 1), ("VIC1",), 5.0, 287),
        (date(2026, 8, 2), ("VIC1",), None, 0),
    ]
    series = rollup_sum(rows, MilestonePeriod.month)[("VIC1",)]
    assert series[datetime(2026, 7, 1)] == BucketValue(value=30.0, interval_count=576)
    assert series[datetime(2026, 8, 1)] == BucketValue(value=5.0, interval_count=287)


def test_attach_interval_counts_joins_on_day_and_key() -> None:
    values = [(date(2026, 7, 1), "VIC1", "battery_discharging", 100.0), (date(2026, 7, 2), "VIC1", "battery_discharging", 50.0)]
    counts = [(date(2026, 7, 1), "VIC1", "battery_discharging", 288)]
    rows = attach_interval_counts(values, counts, ["network_region", "fueltech_group_id"])
    assert rows == [
        (date(2026, 7, 1), ("VIC1", "battery_discharging"), 100.0, 288),
        (date(2026, 7, 2), ("VIC1", "battery_discharging"), 50.0, 0),
    ]


def test_rollup_proportion_null_unless_complete() -> None:
    # NEM network: 5 regions x 288 intervals = 1440 complete pairs for a full day
    rows = [
        (date(2026, 9, 1), (), 600.0, 1000.0, 1440),
        (date(2026, 9, 2), (), 900.0, 1000.0, 1439),
    ]
    series = rollup_proportion(rows, MilestonePeriod.day, NetworkNEM, by_region=False)[()]
    assert series[datetime(2026, 9, 1)] == BucketValue(value=60.0, interval_count=288)
    assert series[datetime(2026, 9, 2)].value is None


def test_rollup_proportion_wem_pre_cutover_exempt_and_clamped() -> None:
    rows = [(date(2022, 6, 1), (), 10.0, 100.0, 48), (date(2026, 6, 1), (), 300.0, 100.0, 288)]
    series = rollup_proportion(rows, MilestonePeriod.day, NetworkWEM, by_region=False)[()]
    assert series[datetime(2022, 6, 1)] == BucketValue(value=10.0, interval_count=288)
    # >200% is the near-zero denominator artifact: -1, never a record
    assert series[datetime(2026, 6, 1)].value == -1


# --- day+ head evaluation -----------------------------------------------------------------------

_END = datetime(2026, 11, 1)


def _eval(
    head: ChainHead, buckets: dict[datetime, BucketValue], end: datetime = _END, tolerances: Tolerances | None = None
) -> HeadFinding:
    spec = head_spec(head)
    assert spec is not None
    return evaluate_period_head(head, spec, buckets, end, tolerances)


def test_vic1_battery_month_high_beaten_by_earlier_month_is_bad() -> None:
    head = _head(
        "au.nem.vic1.battery_discharging.energy.month.high",
        datetime(2026, 10, 1),
        124_943,
        network_region="VIC1",
        fueltech_id="battery_discharging",
    )
    finding = _eval(head, _months({"2026-08-01": 125_160, "2026-09-01": 110_000, "2026-10-01": 124_943}))
    assert finding.status == AuditStatus.bad
    assert finding.best_interval == datetime(2026, 8, 1)
    assert finding.best_value == 125_160
    assert "earlier" in finding.reason


def test_head_still_rank_one_is_ok() -> None:
    head = _head("au.nem.battery_charging.energy.month.high", datetime(2026, 8, 1), 605_508, fueltech_id="battery_charging")
    finding = _eval(head, _months({"2026-07-01": 579_688, "2026-08-01": 605_600}))
    assert finding.status == AuditStatus.ok
    assert finding.recomputed == 605_600


def test_tie_within_rounding_is_not_beaten() -> None:
    head = _head("au.nem.battery_charging.energy.month.high", datetime(2026, 8, 1), 605_508, fueltech_id="battery_charging")
    finding = _eval(head, _months({"2026-07-01": 605_508.3, "2026-08-01": 605_508.0}))
    assert finding.status == AuditStatus.ok


def test_value_drift_still_rank_one_is_suspect() -> None:
    head = _head(
        "au.nem.qld1.battery_charging.energy.month.high",
        datetime(2026, 7, 1),
        193_048,
        network_region="QLD1",
        fueltech_id="battery_charging",
    )
    finding = _eval(head, _months({"2026-06-01": 150_000, "2026-07-01": 223_689}))
    assert finding.status == AuditStatus.suspect
    assert finding.drift_pct is not None and finding.drift_pct > 15


def test_wem_solar_day_high_inflated_head_beaten_by_later_day_is_bad() -> None:
    head = _head(
        "au.wem.solar.energy.day.high", datetime(2024, 11, 26), 26_182, period="day", network_id="WEM", fueltech_id="solar"
    )
    buckets = {
        datetime(2024, 11, 26): BucketValue(value=19_070, interval_count=288),
        datetime(2025, 12, 1): BucketValue(value=22_469, interval_count=288),
    }
    finding = _eval(head, buckets)
    assert finding.status == AuditStatus.bad
    assert finding.recomputed == 19_070
    assert "later" in finding.reason


def test_buckets_before_fueltech_cutoff_do_not_count() -> None:
    # the solar cutoff is 2015-10-26: the whole Oct 2015 month bucket is outside the chain
    head = _head("au.nem.solar.energy.month.high", datetime(2016, 1, 1), 500_000, fueltech_id="solar")
    finding = _eval(head, _months({"2015-10-01": 900_000, "2016-01-01": 500_000}))
    assert finding.status == AuditStatus.ok


def test_current_partial_bucket_is_trimmed() -> None:
    head = _head("au.nem.solar.energy.month.high", datetime(2026, 1, 1), 500_000, fueltech_id="solar")
    finding = _eval(head, _months({"2026-01-01": 500_000, "2026-11-01": 900_000}), end=datetime(2026, 11, 1))
    assert finding.status == AuditStatus.ok


def test_low_ignores_incomplete_buckets() -> None:
    head = _head(
        "au.wem.coal.energy.month.low", datetime(2024, 11, 1), 323_877, aggregate=LOW, network_id="WEM", fueltech_id="coal"
    )
    buckets = {
        datetime(2024, 11, 1): BucketValue(value=323_877, interval_count=8640),
        # lower, but a 30-minute-era month fails the 8000-interval low guard, like the backlog
        datetime(2022, 11, 1): BucketValue(value=298_667, interval_count=1440),
    }
    assert _eval(head, buckets).status == AuditStatus.ok


def test_low_beaten_by_complete_bucket_is_bad() -> None:
    head = _head(
        "au.nem.sa1.gas.emissions.day.low",
        datetime(2026, 7, 12),
        415.0264,
        metric="emissions",
        period="day",
        aggregate=LOW,
        network_region="SA1",
        fueltech_id="gas",
    )
    buckets = {
        datetime(2026, 5, 30): BucketValue(value=401.57, interval_count=288),
        datetime(2026, 7, 12): BucketValue(value=415.0264, interval_count=288),
    }
    finding = _eval(head, buckets)
    assert finding.status == AuditStatus.bad
    assert finding.recomputed == pytest.approx(415.0264)


def test_low_values_compared_unrounded() -> None:
    # the backlog stores lows unrounded: 0.3394 vs 0.3394 is not a 100% drift
    head = _head(
        "au.nem.bioenergy.emissions.day.low",
        datetime(2009, 12, 20),
        0.3394,
        metric="emissions",
        period="day",
        aggregate=LOW,
        fueltech_id="bioenergy",
    )
    finding = _eval(head, {datetime(2009, 12, 20): BucketValue(value=0.3394, interval_count=288)})
    assert finding.status == AuditStatus.ok


def test_small_absolute_drift_is_not_suspect() -> None:
    head = _head(
        "au.nem.tas1.gas.energy.day.low",
        datetime(2007, 2, 26),
        0.1134,
        period="day",
        aggregate=LOW,
        network_region="TAS1",
        fueltech_id="gas",
    )
    finding = _eval(head, {datetime(2007, 2, 26): BucketValue(value=0.2, interval_count=288)})
    assert finding.status == AuditStatus.ok


def test_low_head_bucket_now_incomplete_is_suspect() -> None:
    head = _head("au.wem.energy.year.low", datetime(2017, 1, 1), 19_438_046, period="year", aggregate=LOW, network_id="WEM")
    buckets = {datetime(2017, 1, 1): BucketValue(value=19_201_839, interval_count=17520)}
    finding = _eval(head, buckets)
    assert finding.status == AuditStatus.suspect
    assert "record guard" in finding.reason


def test_head_bucket_missing() -> None:
    head = _head(
        "au.nem.qld1.renewables.proportion.day.high",
        datetime(2026, 10, 3),
        53.32,
        metric="renewable_proportion",
        period="day",
        network_region="QLD1",
    )
    assert _eval(head, {datetime(2026, 9, 30): BucketValue(value=51.61, interval_count=288)}).status == AuditStatus.suspect
    assert _eval(head, {datetime(2026, 9, 30): BucketValue(value=60.0, interval_count=288)}).status == AuditStatus.bad


# --- interval head evaluation -------------------------------------------------------------------


def _interval_head(stored: float, prev_value: float) -> ChainHead:
    return _head(
        "au.wem.renewables.power.interval.high",
        datetime(2026, 10, 28, 11, 40),
        stored,
        metric="power",
        period="interval",
        network_id="WEM",
        fueltech_id="renewables",
        significance=10,
        prev_interval=datetime(2026, 10, 28, 11, 0),
        prev_value=prev_value,
    )


def _eval_interval(head: ChainHead, recomputed: float | None, recomputed_prev: float | None) -> HeadFinding:
    spec = head_spec(head)
    assert spec is not None
    return evaluate_interval_head(head, spec, recomputed, recomputed_prev)


def test_wem_renewables_interval_high_no_longer_beats_predecessor_is_bad() -> None:
    finding = _eval_interval(_interval_head(3317, 3308), recomputed=3222.0, recomputed_prev=3274.59)
    assert finding.status == AuditStatus.bad
    assert finding.best_interval == datetime(2026, 10, 28, 11, 0)
    assert "no longer beats previous" in finding.reason


def test_interval_head_ok_and_suspect_and_missing() -> None:
    assert _eval_interval(_interval_head(3317, 3308), 3317.2, 3308.0).status == AuditStatus.ok
    assert _eval_interval(_interval_head(3317, 3000), 3250.0, 3000.0).status == AuditStatus.suspect
    assert _eval_interval(_interval_head(3317, 3000), None, 3000.0).status == AuditStatus.suspect
    # predecessor gone from the data: fall back to its stored value
    assert _eval_interval(_interval_head(3317, 3400), 3317.0, None).status == AuditStatus.bad


# --- selection and filters ----------------------------------------------------------------------


def test_select_heads_significance_or_month() -> None:
    heads = [
        _head("a", datetime(2026, 1, 1), 1, period="day", significance=6),
        _head("b", datetime(2026, 1, 1), 1, period="month", significance=3),
        _head("c", datetime(2026, 1, 1), 1, period="day", significance=7, network_id="WEM"),
    ]
    assert [h.record_id for h in select_heads(heads, 7)] == ["b", "c"]
    assert [h.record_id for h in select_heads(heads, 7, ["wem"])] == ["c"]


def test_filter_since_keeps_heads_and_beaten_by_after() -> None:
    def finding(interval: datetime, best: datetime | None) -> HeadFinding:
        return HeadFinding(
            record_id=f"{interval:%Y%m%d}",
            interval=interval,
            period="day",
            aggregate="high",
            significance=8,
            network_id="NEM",
            status=AuditStatus.bad,
            stored=1,
            best_interval=best,
        )

    since = datetime(2026, 10, 27)
    kept = filter_since(
        [
            finding(datetime(2026, 10, 28), None),
            finding(datetime(2024, 11, 26), datetime(2026, 10, 30)),
            finding(datetime(2024, 1, 1), datetime(2025, 1, 1)),
        ],
        since,
    )
    assert [f.record_id for f in kept] == ["20261028", "20241126"]


def test_reminder_line() -> None:
    assert (
        head_audit_reminder(datetime(2026, 10, 27, 5))
        == "run the milestone head audit: opennem milestones audit-heads --since 2026-10-27"
    )
    assert head_audit_reminder(None).endswith("--since <repair start>")


# --- end to end against a fake clickhouse ---------------------------------------------------------


class _FakeClickHouse:
    """Answers the audit's queries from canned rows, keyed on the table the query reads."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> list[tuple[Any, ...]]:
        self.queries.append(query)
        days = [date(2026, 7, 1) + timedelta(days=i) for i in range(123)]  # Jul..Oct 2026

        if "FROM fueltech_intervals_daily_mv FINAL" in query:
            # VIC1 battery discharging: Aug totals 125,160, Oct 124,943 (Oct is the stored head)
            daily = {7: 100_000, 8: 125_160, 9: 110_000, 10: 124_943}
            per_day = {d: daily[d.month] / (31 if d.month in (7, 8, 10) else 30) for d in days}
            return [(d, "VIC1", "battery_discharging", v) for d, v in per_day.items()]

        if "FROM fueltech_intervals_mv" in query and "uniqExact(interval)" in query:
            return [(d, "VIC1", "battery_discharging", 288) for d in days]

        if "FROM market_summary FINAL" in query:
            # (date, demand_energy, intervals, generation_renewable, demand_gross, complete_pairs)
            return [(d, 400_000.0, 288, 600.0 if d.month == 9 else 400.0, 1000.0, 1440) for d in days]

        if "FROM renewable_intervals_mv FINAL" in query:
            # interval point query: (time_bucket, renewable, value, interval_count)
            if "2026-10-28 11:40:00" in query:
                return [(datetime(2026, 10, 28, 11, 40), True, 3222.0, 1), (datetime(2026, 10, 28, 11, 40), False, 500.0, 1)]
            if "2026-10-28 11:00:00" in query:
                return [(datetime(2026, 10, 28, 11, 0), True, 3274.59, 1)]

        raise AssertionError(f"unexpected query: {query}")


@pytest.mark.asyncio
async def test_audit_heads_end_to_end_with_fake_clickhouse() -> None:
    heads = [
        _head(
            "au.nem.vic1.battery_discharging.energy.month.high",
            datetime(2026, 10, 1),
            124_943,
            network_region="VIC1",
            fueltech_id="battery_discharging",
            significance=9,
        ),
        _head(
            "au.nem.renewables.proportion.month.high", datetime(2026, 9, 1), 60.0, metric="renewable_proportion", significance=5
        ),
        _interval_head(3317, 3308),
        # below the significance floor and not a month: never queried
        _head("au.nem.coal.energy.day.high", datetime(2026, 7, 1), 1, period="day", fueltech_id="coal", significance=3),
    ]
    client = _FakeClickHouse()
    findings = await audit_heads(
        heads=heads, client=client, now={"NEM": datetime(2026, 11, 2, 10), "WEM": datetime(2026, 11, 2, 8)}
    )

    by_id = {f.record_id: f for f in findings}
    assert set(by_id) == {
        "au.nem.vic1.battery_discharging.energy.month.high",
        "au.nem.renewables.proportion.month.high",
        "au.wem.renewables.power.interval.high",
    }
    assert by_id["au.nem.vic1.battery_discharging.energy.month.high"].status == AuditStatus.bad
    assert by_id["au.nem.vic1.battery_discharging.energy.month.high"].best_interval == datetime(2026, 8, 1)
    assert by_id["au.nem.renewables.proportion.month.high"].status == AuditStatus.ok
    assert by_id["au.wem.renewables.power.interval.high"].status == AuditStatus.bad
    # BAD sorts first
    assert findings[-1].status == AuditStatus.ok

    # read only, FINAL-scoped value reads, and the daily series is fetched once per (network, source, grouping)
    joined = "\n".join(client.queries).upper()
    for verb in ("INSERT", "ALTER", "DELETE", "OPTIMIZE", "DROP"):
        assert verb not in joined
    assert sum("FUELTECH_INTERVALS_DAILY_MV FINAL" in q.upper() for q in client.queries) == 1
    assert sum("MARKET_SUMMARY FINAL" in q.upper() for q in client.queries) == 1
    # the region filter keeps the NT1 backfill rooftop rows out of NEM totals, like the backlog
    assert all("network_region IN" in q for q in client.queries if "NEM" in q)


# --- memoised bucket lookup: identical to the per-row bucket_start rollups (BACKEND-6A6/6B3) -------


def _old_rollup_sum(rows: list[tuple[Any, ...]], period: MilestonePeriod) -> dict[tuple[Any, ...], dict[datetime, BucketValue]]:
    """rollup_sum as it was before the memoised lookup: bucket_start per row."""
    values: dict[tuple[Any, ...], dict[datetime, float | None]] = defaultdict(dict)
    counts: dict[tuple[Any, ...], dict[datetime, int]] = defaultdict(lambda: defaultdict(int))
    for day, key, value, interval_count in rows:
        bucket = bucket_start(day, period)
        if value is not None:
            values[key][bucket] = (values[key].get(bucket) or 0.0) + float(value)
        else:
            values[key].setdefault(bucket, None)
        counts[key][bucket] += int(interval_count or 0)
    return {
        key: {bucket: BucketValue(value=v, interval_count=counts[key][bucket]) for bucket, v in buckets.items()}
        for key, buckets in values.items()
    }


def _old_rollup_proportion(
    rows: list[tuple[Any, ...]], period: MilestonePeriod, network: Any, by_region: bool
) -> dict[tuple[Any, ...], dict[datetime, BucketValue]]:
    """rollup_proportion as it was: same body, bucket_start per row."""
    sums: dict[tuple[Any, ...], dict[datetime, list[float]]] = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0]))
    for day, key, gen, demand_gross, pairs in rows:
        acc = sums[key][bucket_start(day, period)]
        acc[0] += float(gen or 0)
        acc[1] += float(demand_gross or 0)
        acc[2] += int(pairs or 0)
    required_regions = 1 if by_region else len(network.regions or [network.code])
    out: dict[tuple[Any, ...], dict[datetime, BucketValue]] = {}
    for key, buckets in sums.items():
        out[key] = {}
        for bucket, (gen, demand_gross, pairs) in buckets.items():
            expected = int((bucket_end(bucket, period) - bucket).total_seconds() // 60) // network.interval_size
            exempt = network == NetworkWEM and bucket < datetime(2023, 10, 1, 8, 0)
            complete = exempt or int(pairs) == expected * required_regions
            out[key][bucket] = BucketValue(
                value=clamp_proportion(gen, demand_gross) if complete else None,
                interval_count=expected if exempt else int(pairs) // required_regions,
            )
    return out


def _synthetic_rows(seed: int) -> list[tuple[Any, ...]]:
    """Several years of daily rows over a few keys, with NULLs, gaps and a few datetime days."""
    rng = random.Random(seed)
    keys = [("NSW1", "coal_black"), ("VIC1", "battery_discharging"), ("QLD1", "solar_utility")]
    rows: list[tuple[Any, ...]] = []
    for i in range(3 * 366):
        day: Any = date(2019, 11, 1) + timedelta(days=i)
        if i % 97 == 0:
            day = datetime(day.year, day.month, day.day, 13, 5)
        for key in keys:
            if rng.random() < 0.05:
                continue  # gap: no row for this day/key
            value = None if rng.random() < 0.05 else rng.uniform(0, 5000)
            rows.append((day, key, value, rng.choice([0, 287, 288, None]), rng.choice([0, 1440, 288, None])))
    rng.shuffle(rows)
    return rows


@pytest.mark.parametrize("period", [MilestonePeriod.day, MilestonePeriod.month, MilestonePeriod.quarter, MilestonePeriod.year])
def test_rollup_sum_memoised_matches_per_row_bucket_start(period: MilestonePeriod) -> None:
    rows = [(d, k, v, c) for d, k, v, c, _ in _synthetic_rows(1)]
    assert rollup_sum(rows, period) == _old_rollup_sum(rows, period)


@pytest.mark.parametrize("period", [MilestonePeriod.day, MilestonePeriod.month, MilestonePeriod.quarter, MilestonePeriod.year])
@pytest.mark.parametrize("network", [NetworkNEM, NetworkWEM])
def test_rollup_proportion_memoised_matches_per_row_bucket_start(period: MilestonePeriod, network: Any) -> None:
    rows = [(d, k, v, (v or 0) * 2, p) for d, k, v, _, p in _synthetic_rows(2)]
    assert rollup_proportion(rows, period, network, by_region=True) == _old_rollup_proportion(rows, period, network, True)
    assert rollup_proportion(rows, period, network, by_region=False) == _old_rollup_proportion(rows, period, network, False)


def test_rollup_series_dispatches_like_the_inline_rollups() -> None:
    fields = ["network_region"]
    # market rows: (date, region, demand_energy, intervals, generation_renewable, demand_gross, complete_pairs)
    market = [(date(2026, 7, 1) + timedelta(days=i), "VIC1", 100.0 + i, 288, 40.0, 100.0, 288) for i in range(62)]
    demand = rollup_series(market, MilestoneType.demand, MilestonePeriod.month, NetworkNEM, fields)
    assert demand == rollup_sum([(r[0], (r[1],), r[2], r[3]) for r in market], MilestonePeriod.month)
    proportion = rollup_series(market, MilestoneType.proportion, MilestonePeriod.month, NetworkNEM, fields)
    assert proportion == rollup_proportion(
        [(r[0], (r[1],), r[4], r[5], r[6]) for r in market], MilestonePeriod.month, NetworkNEM, by_region=True
    )
    generation = [(r[0], (r[1],), r[2], r[3]) for r in market]
    assert rollup_series(generation, MilestoneType.energy, MilestonePeriod.month, NetworkNEM, fields) == rollup_sum(
        generation, MilestonePeriod.month
    )


@pytest.mark.asyncio
async def test_audit_heads_rolls_up_off_the_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    import opennem.recordreactor.head_audit as head_audit

    loop_thread = threading.get_ident()
    rollup_threads: list[int] = []
    real_rollup_sum = head_audit.rollup_sum

    def spy(*args: Any, **kwargs: Any) -> Any:
        rollup_threads.append(threading.get_ident())
        return real_rollup_sum(*args, **kwargs)

    monkeypatch.setattr(head_audit, "rollup_sum", spy)
    head = _head(
        "au.nem.vic1.battery_discharging.energy.month.high",
        datetime(2026, 10, 1),
        124_943,
        network_region="VIC1",
        fueltech_id="battery_discharging",
        significance=9,
    )
    findings = await audit_heads(
        heads=[head], client=_FakeClickHouse(), now={"NEM": datetime(2026, 11, 2, 10), "WEM": datetime(2026, 11, 2, 8)}
    )
    assert findings[0].status == AuditStatus.bad
    assert rollup_threads and loop_thread not in rollup_threads


@pytest.mark.asyncio
async def test_audit_heads_since_filters_untouched_heads() -> None:
    heads = [
        _head(
            "au.nem.vic1.battery_discharging.energy.month.high",
            datetime(2026, 10, 1),
            124_943,
            network_region="VIC1",
            fueltech_id="battery_discharging",
        )
    ]
    findings = await audit_heads(
        heads=heads, client=_FakeClickHouse(), since=datetime(2026, 11, 1), now={"NEM": datetime(2026, 11, 2, 10)}
    )
    # head is 2026-10 and the month beating it is 2026-08: a repair from 2026-11 touched neither
    assert findings == []


def test_filter_since_keeps_month_head_whose_bucket_holds_the_repair() -> None:
    month_head = HeadFinding(
        record_id="au.nem.vic1.battery_discharging.energy.month.high",
        interval=datetime(2026, 10, 1),
        period="month",
        aggregate="high",
        significance=9,
        network_id="NEM",
        status=AuditStatus.bad,
        stored=124_943,
        best_interval=datetime(2026, 8, 1),
    )
    assert filter_since([month_head], datetime(2026, 10, 27)) == [month_head]
    assert filter_since([month_head], datetime(2026, 11, 1)) == []


def test_price_day_head_is_unsupported() -> None:
    assert head_spec(_head("au.nem.price.day.high", datetime(2026, 1, 1), 1, metric="price", period="day")) is None
