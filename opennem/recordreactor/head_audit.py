"""Milestone chain head audit (#786).

Milestones are derived data. A record is minted from the data as it stood at the time, and nothing
re-checks it after a data repair or re-aggregation, so a head can end up sitting on numbers that no
longer exist: the 2026-11-02 validation found five significance 7+ heads that were false after the
APVI WA repair and the energy re-aggregation (a VIC1 battery month high now beaten by an earlier
month, NEM battery month highs beaten by a re-aggregated July, WEM renewables interval highs revised
down, a WEM solar day high inflated by the old APVI flat tail that was blocking genuine records).

This module re-derives each chain head from the settled series and reports, it never writes:

- day+ heads: the full bucket series is rebuilt from the daily MVs (`*_intervals_daily_mv FINAL` for
  generation, `market_summary FINAL` per day for demand and proportion) and rolled up in Python with
  the backlog's own rules (metric and fueltech cutoffs, low completeness guard, maxes floor, the
  proportion completeness guard, trim to the last complete bucket). The head is checked for value
  drift and for still being rank 1 across the chain's history.
- interval heads: the head and its predecessor are recomputed at their intervals with the
  incremental path's query (`FINAL`, scoped to the one interval), and the head must still beat the
  predecessor. A full-history rank check at interval resolution would cost a full rebuild scan.

Findings are OK, SUSPECT (value drifted or the head bucket is no longer complete, but it is still the
record) or BAD (the head is no longer the record). The comparison logic is pure; the I/O is at the
bottom of the module.

Run it after any repair: `opennem milestones audit-heads --since <repair start>`. A daily alert-only
cron runs it too (`opennem.monitors.milestone_head_audit`).
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any, cast

from sqlalchemy import text

from opennem.queries.utils import list_to_case
from opennem.recordreactor.metric_registry import (
    GROUPING_FUELTECH,
    GROUPING_NETWORK,
    GROUPING_REGION,
    GROUPING_REGION_FUELTECH,
    GROUPING_REGION_RENEWABLE,
    GROUPING_RENEWABLE,
    GroupingConfig,
    get_fueltech_date_cutoffs,
    get_metric_registry,
    get_network_region_filter_sql,
)
from opennem.recordreactor.queries_incremental import build_period_aggregation_query
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestonePeriod,
    MilestoneType,
)
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM

logger = logging.getLogger("opennem.recordreactor.head_audit")

DEFAULT_MIN_SIGNIFICANCE = 7
# stored vs recomputed head value, as a percentage of the stored value: above this is SUSPECT
DEFAULT_VALUE_TOLERANCE_PCT = 0.5
# how far another bucket has to beat the head, as a percentage, before the head counts as beaten.
# Anything inside the stored rounding is always a tie (see `_rank_epsilon`)
DEFAULT_RANK_TOLERANCE_PCT = 0.01
# interval heads younger than this may still be waiting on rooftop (#652), so they are not audited
INTERVAL_SETTLE_HOURS = 3

AUDITED_PERIODS = (
    MilestonePeriod.interval,
    MilestonePeriod.day,
    MilestonePeriod.month,
    MilestonePeriod.quarter,
    MilestonePeriod.year,
)

# --- backlog rules, mirrored from backlog._analyze_milestone_records -------------------------------

# metric-wide earliest bucket (backlog `date_cutoffs`, applied to the bucket start)
_METRIC_CUTOFFS: dict[MilestoneType, datetime] = {
    MilestoneType.power: datetime(2000, 1, 1),
    MilestoneType.energy: datetime(2000, 1, 1),
    MilestoneType.emissions: datetime(2000, 1, 1),
    MilestoneType.price: datetime(2009, 7, 1),
    MilestoneType.demand: datetime(2009, 7, 1),
    MilestoneType.proportion: datetime(2007, 6, 1),
}

# minimum interval count for a bucket to hold a LOW record (backlog IntervalThresholds)
_LOW_INTERVAL_THRESHOLDS: dict[MilestonePeriod, int] = {
    MilestonePeriod.interval: 1,
    MilestonePeriod.day: 288,
    MilestonePeriod.month: 8000,
    MilestonePeriod.quarter: 24000,
    MilestonePeriod.year: 98000,
}

# see metric_registry._WEM_FIVE_MINUTE_FROM: WEM proportion buckets before this skip completeness
_WEM_FIVE_MINUTE_FROM = datetime(2023, 10, 1, 8, 0)

_GENERATION_METRICS = (MilestoneType.power, MilestoneType.energy, MilestoneType.emissions)
_GROUPINGS_BY_FIELDS: dict[tuple[str, ...], GroupingConfig] = {
    tuple(g.group_by_fields): g
    for g in (
        GROUPING_NETWORK,
        GROUPING_REGION,
        GROUPING_FUELTECH,
        GROUPING_RENEWABLE,
        GROUPING_REGION_FUELTECH,
        GROUPING_REGION_RENEWABLE,
    )
}
_NETWORKS: dict[str, NetworkSchema] = {"NEM": NetworkNEM, "WEM": NetworkWEM}


def maxes_floor(metric: MilestoneType) -> float:
    """Backlog `maxes_min_value`: a bucket must round above this to hold a HIGH record."""
    if metric in (MilestoneType.energy, MilestoneType.emissions):
        return 1000
    if metric == MilestoneType.proportion:
        return 0
    return 100


def round_to(metric: MilestoneType) -> int:
    """Backlog rounding of the bucket value before it is compared and stored."""
    return 2 if metric == MilestoneType.proportion else 0


def as_stored(value: float, metric: MilestoneType, aggregate: MilestoneAggregate) -> float:
    """A bucket value the way the backlog stores it: highs are rounded (running_maxes), lows are not.

    Proportion is rounded to 2 places in the value expression itself, so both of its aggregates are.
    """
    if aggregate == MilestoneAggregate.high or metric == MilestoneType.proportion:
        return round(value, round_to(metric))
    return value


# absolute drift below this is never SUSPECT: lows near zero (0.2 vs 0.3 MWh) swing by 100%
_DRIFT_ABS_FLOOR = 1.0
_DRIFT_ABS_FLOOR_PROPORTION = 0.05


# --- data shapes ------------------------------------------------------------------------------------


class AuditStatus(StrEnum):
    ok = "OK"
    suspect = "SUSPECT"
    bad = "BAD"


@dataclass(frozen=True, slots=True)
class ChainHead:
    """The latest entry of a milestone chain, with its predecessor."""

    record_id: str
    interval: datetime
    aggregate: MilestoneAggregate
    metric: str
    period: str
    significance: int
    value: float
    network_id: str
    network_region: str | None = None
    fueltech_id: str | None = None
    instance_id: uuid.UUID | None = None
    prev_interval: datetime | None = None
    prev_value: float | None = None


@dataclass(frozen=True, slots=True)
class HeadSpec:
    """What series a head belongs to: enough to recompute it."""

    network: NetworkSchema
    metric: MilestoneType  # the source metric: demand chains are stored as energy/power + fueltech demand
    period: MilestonePeriod
    grouping: GroupingConfig
    key: tuple[Any, ...]  # grouping values, in grouping.group_by_fields order


@dataclass(frozen=True, slots=True)
class BucketValue:
    value: float | None
    interval_count: int


@dataclass(frozen=True, slots=True)
class HeadFinding:
    record_id: str
    interval: datetime
    period: str
    aggregate: str
    significance: int
    network_id: str
    status: AuditStatus
    stored: float
    recomputed: float | None = None
    best_interval: datetime | None = None
    best_value: float | None = None
    reason: str = ""

    @property
    def drift_pct(self) -> float | None:
        if self.recomputed is None:
            return None
        return _drift_pct(self.stored, self.recomputed)


@dataclass(frozen=True, slots=True)
class Tolerances:
    value_pct: float = DEFAULT_VALUE_TOLERANCE_PCT
    rank_pct: float = DEFAULT_RANK_TOLERANCE_PCT


# --- pure logic -----------------------------------------------------------------------------------


def head_spec(head: ChainHead) -> HeadSpec | None:
    """Map a stored head to its series. None for periods/networks/metrics the audit does not cover."""
    network = _NETWORKS.get((head.network_id or "").upper())
    if network is None:
        return None

    try:
        period = MilestonePeriod(head.period)
    except ValueError:
        return None
    if period not in AUDITED_PERIODS:
        return None

    try:
        metric = MilestoneType(head.metric)
    except ValueError:
        return None

    fields: list[str] = []
    key: list[Any] = []

    if head.network_region:
        fields.append("network_region")
        key.append(head.network_region)

    fueltech = head.fueltech_id
    if fueltech == MilestoneFueltechGrouping.demand.value:
        # demand chains are stored as energy (day+) / power (interval) with fueltech "demand"
        metric = MilestoneType.demand
    elif fueltech in (MilestoneFueltechGrouping.renewables.value, MilestoneFueltechGrouping.fossils.value):
        fields.append("renewable")
        key.append(fueltech == MilestoneFueltechGrouping.renewables.value)
    elif fueltech:
        fields.append("fueltech_group_id")
        key.append(fueltech)

    if metric == MilestoneType.market_value:
        return None
    if metric in (MilestoneType.power, MilestoneType.price) and period != MilestonePeriod.interval:
        return None
    if metric in (MilestoneType.energy, MilestoneType.emissions) and period == MilestonePeriod.interval:
        return None

    grouping = _GROUPINGS_BY_FIELDS.get(tuple(fields))
    if grouping is None:
        return None

    return HeadSpec(network=network, metric=metric, period=period, grouping=grouping, key=tuple(key))


def normalise_key(fields: Sequence[str], values: Sequence[Any]) -> tuple[Any, ...]:
    """Grouping values from a ClickHouse row, comparable with `HeadSpec.key` (renewable as bool)."""
    return tuple(bool(v) if f == "renewable" else v for f, v in zip(fields, values, strict=True))


def bucket_start(day: date | datetime, period: MilestonePeriod) -> datetime:
    """Start of the period bucket holding `day`, as a naive midnight datetime (network time)."""
    d = day.date() if isinstance(day, datetime) else day
    if period == MilestonePeriod.day:
        start = d
    elif period == MilestonePeriod.month:
        start = d.replace(day=1)
    elif period == MilestonePeriod.quarter:
        start = d.replace(month=3 * ((d.month - 1) // 3) + 1, day=1)
    elif period == MilestonePeriod.year:
        start = d.replace(month=1, day=1)
    else:
        raise ValueError(f"No day+ bucket for period {period}")
    return datetime(start.year, start.month, start.day)


def _bucket_lookup(period: MilestonePeriod) -> Callable[[date | datetime], datetime]:
    """`bucket_start` memoised per day for one rollup: daily rows repeat each day once per group.

    A full-history region x fueltech series is hundreds of thousands of rows over ~10k distinct days,
    and the per-row date arithmetic was most of the rollup's CPU (BACKEND-6A6/6B3).
    """
    cache: dict[date | datetime, datetime] = {}

    def lookup(day: date | datetime) -> datetime:
        bucket = cache.get(day)
        if bucket is None:
            bucket = cache[day] = bucket_start(day, period)
        return bucket

    return lookup


def bucket_end(start: datetime, period: MilestonePeriod) -> datetime:
    """Exclusive end of the bucket starting at `start`."""
    if period == MilestonePeriod.day:
        return start + timedelta(days=1)
    months = {MilestonePeriod.month: 1, MilestonePeriod.quarter: 3, MilestonePeriod.year: 12}.get(period)
    if months is None:
        raise ValueError(f"No day+ bucket for period {period}")
    month_index = start.month - 1 + months
    return start.replace(year=start.year + month_index // 12, month=month_index % 12 + 1)


def series_cutoff(metric: MilestoneType, key_fields: Sequence[str], key: Sequence[Any]) -> datetime:
    """Earliest bucket start a chain can use: the metric cutoff, raised by a fueltech cutoff.

    Mirrors the backlog: `date_cutoffs` plus `get_fueltech_cutoff_sql`, both applied to the bucket
    start, so a month that straddles the solar cutoff (2015-10) is excluded whole.
    """
    cutoff = _METRIC_CUTOFFS[metric]
    cutoffs = get_fueltech_date_cutoffs()
    values = dict(zip(key_fields, key, strict=True))

    if "fueltech_group_id" in values:
        fueltech = values["fueltech_group_id"]
        if fueltech not in (MilestoneFueltechGrouping.renewables.value, MilestoneFueltechGrouping.fossils.value):
            cutoff = max(cutoff, cutoffs.get(fueltech, cutoff))
    if values.get("renewable") is True:
        renewables_cutoff = cutoffs.get(MilestoneFueltechGrouping.renewables.value)
        if renewables_cutoff:
            cutoff = max(cutoff, renewables_cutoff)

    return cutoff


def rollup_sum(
    rows: Iterable[tuple[date, tuple[Any, ...], float | None, int]], period: MilestonePeriod
) -> dict[tuple[Any, ...], dict[datetime, BucketValue]]:
    """(day, key, value, interval_count) daily rows -> {key: {bucket: summed value and count}}.

    Days are disjoint, so summing the per-day distinct interval counts gives the bucket's distinct
    count (the backlog's `count(distinct interval)`). A bucket whose days are all NULL is NULL.
    """
    values: dict[tuple[Any, ...], dict[datetime, float | None]] = defaultdict(dict)
    counts: dict[tuple[Any, ...], dict[datetime, int]] = defaultdict(lambda: defaultdict(int))
    bucket_of = _bucket_lookup(period)

    for day, key, value, interval_count in rows:
        bucket = bucket_of(day)
        if value is not None:
            values[key][bucket] = (values[key].get(bucket) or 0.0) + float(value)
        else:
            values[key].setdefault(bucket, None)
        counts[key][bucket] += int(interval_count or 0)

    return {
        key: {bucket: BucketValue(value=v, interval_count=counts[key][bucket]) for bucket, v in buckets.items()}
        for key, buckets in values.items()
    }


def clamp_proportion(generation_renewable: float, demand_gross: float) -> float:
    """metric_registry.PROPORTION_CLAMPED_SQL: percent, -1 when the denominator is unusable or >200%."""
    if demand_gross > 0:
        pct = generation_renewable / demand_gross * 100
        if pct <= 200:
            return round(pct, 2)
    return -1


def rollup_proportion(
    rows: Iterable[tuple[date, tuple[Any, ...], float | None, float | None, int]],
    period: MilestonePeriod,
    network: NetworkSchema,
    by_region: bool,
) -> dict[tuple[Any, ...], dict[datetime, BucketValue]]:
    """(day, key, generation_renewable, demand_gross, complete_pairs) daily rows -> proportion buckets.

    Same rule as `get_proportion_sql`: NULL unless every (interval, region) of the bucket has both
    inputs, counted against the bucket's real length; WEM buckets before the 5-minute cutover are
    exempt and count as complete.
    """
    sums: dict[tuple[Any, ...], dict[datetime, list[float]]] = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0]))
    bucket_of = _bucket_lookup(period)

    for day, key, gen, demand_gross, pairs in rows:
        acc = sums[key][bucket_of(day)]
        acc[0] += float(gen or 0)
        acc[1] += float(demand_gross or 0)
        acc[2] += int(pairs or 0)

    required_regions = 1 if by_region else len(network.regions or [network.code])
    out: dict[tuple[Any, ...], dict[datetime, BucketValue]] = {}

    for key, buckets in sums.items():
        out[key] = {}
        for bucket, (gen, demand_gross, pairs) in buckets.items():
            expected = int((bucket_end(bucket, period) - bucket).total_seconds() // 60) // network.interval_size
            exempt = network == NetworkWEM and bucket < _WEM_FIVE_MINUTE_FROM
            complete = exempt or int(pairs) == expected * required_regions
            out[key][bucket] = BucketValue(
                value=clamp_proportion(gen, demand_gross) if complete else None,
                interval_count=expected if exempt else int(pairs) // required_regions,
            )

    return out


def rollup_series(
    rows: Sequence[Sequence[Any]],
    metric: MilestoneType,
    period: MilestonePeriod,
    network: NetworkSchema,
    fields: Sequence[str],
) -> dict[tuple[Any, ...], dict[datetime, BucketValue]]:
    """Roll a cached daily source (market rows, or joined generation rows) up into one series."""
    n = len(fields)
    if metric == MilestoneType.proportion:
        # (date, group..., demand_energy, intervals, generation_renewable, demand_gross, complete_pairs)
        return rollup_proportion(
            ((r[0], normalise_key(fields, r[1 : 1 + n]), r[n + 3], r[n + 4], r[n + 5]) for r in rows),
            period,
            network,
            by_region="network_region" in fields,
        )
    if metric == MilestoneType.demand:
        return rollup_sum(((r[0], normalise_key(fields, r[1 : 1 + n]), r[n + 1], r[n + 2]) for r in rows), period)
    # generation rows are already (date, key, value, intervals)
    return rollup_sum(cast(Iterable[tuple[date, tuple[Any, ...], float | None, int]], rows), period)


def drifted(stored: float, recomputed: float, metric: MilestoneType, tolerances: Tolerances) -> bool:
    """Recomputed differs from stored by more than the value tolerance and the absolute floor."""
    floor = _DRIFT_ABS_FLOOR_PROPORTION if metric == MilestoneType.proportion else _DRIFT_ABS_FLOOR
    return abs(recomputed - stored) > max(floor, abs(stored) * tolerances.value_pct / 100)


def _drift_pct(stored: float, recomputed: float) -> float:
    return (recomputed - stored) / max(abs(stored), 1e-9) * 100


def _rank_epsilon(reference: float, metric: MilestoneType, tolerances: Tolerances) -> float:
    """Margin another value needs to count as beating `reference`: the stored rounding at least."""
    return max(0.5 * 10 ** -round_to(metric), abs(reference) * tolerances.rank_pct / 100)


def beats(
    challenger: float, reference: float, aggregate: MilestoneAggregate, metric: MilestoneType, tolerances: Tolerances
) -> bool:
    """True when `challenger` is a better record than `reference` by more than the rank tolerance."""
    margin = challenger - reference if aggregate == MilestoneAggregate.high else reference - challenger
    return margin > _rank_epsilon(reference, metric, tolerances)


def eligible(bucket: BucketValue, aggregate: MilestoneAggregate, metric: MilestoneType, period: MilestonePeriod) -> bool:
    """Whether a bucket can hold a record, by the backlog's guards."""
    if bucket.value is None:
        return False
    if aggregate == MilestoneAggregate.high:
        return round(bucket.value) > maxes_floor(metric)
    if metric != MilestoneType.price and bucket.value <= 0:
        return False
    return bucket.interval_count >= _LOW_INTERVAL_THRESHOLDS.get(period, 1)


def best_bucket(
    buckets: dict[datetime, BucketValue],
    aggregate: MilestoneAggregate,
    metric: MilestoneType,
    period: MilestonePeriod,
    cutoff: datetime,
    end_exclusive: datetime,
) -> tuple[datetime, float] | None:
    """The record bucket of a series: argmax/argmin over eligible buckets in [cutoff, end). Earliest wins ties."""
    candidates = [
        (bucket, as_stored(b.value, metric, aggregate))
        for bucket, b in buckets.items()
        if cutoff <= bucket < end_exclusive and b.value is not None and eligible(b, aggregate, metric, period)
    ]
    if not candidates:
        return None
    sign = -1 if aggregate == MilestoneAggregate.high else 1
    return min(candidates, key=lambda c: (sign * c[1], c[0]))


def _finding(head: ChainHead, status: AuditStatus, reason: str, **kwargs: Any) -> HeadFinding:
    return HeadFinding(
        record_id=head.record_id,
        interval=head.interval,
        period=head.period,
        aggregate=head.aggregate.value,
        significance=head.significance,
        network_id=head.network_id,
        status=status,
        stored=float(head.value),
        reason=reason,
        **kwargs,
    )


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}" if abs(value) < 100 else f"{value:,.0f}"


def evaluate_period_head(
    head: ChainHead,
    spec: HeadSpec,
    buckets: dict[datetime, BucketValue] | None,
    end_exclusive: datetime,
    tolerances: Tolerances | None = None,
) -> HeadFinding:
    """Check a day+ head against its rebuilt series: value drift and rank 1 in the chain's history."""
    tolerances = tolerances or Tolerances()
    metric, period, aggregate = spec.metric, spec.period, head.aggregate
    cutoff = series_cutoff(metric, spec.grouping.group_by_fields, spec.key)
    head_bucket = bucket_start(head.interval, period)
    buckets = buckets or {}
    best = best_bucket(buckets, aggregate, metric, period, cutoff, end_exclusive)
    best_kwargs: dict[str, Any] = {"best_interval": best[0], "best_value": best[1]} if best else {}

    current = buckets.get(head_bucket)
    if current is None or current.value is None:
        if best and best[0] != head_bucket and beats(best[1], head.value, aggregate, metric, tolerances):
            return _finding(
                head,
                AuditStatus.bad,
                f"head bucket has no data now; {best[0]:%Y-%m-%d} {_fmt(best[1])} beats the stored value",
                **best_kwargs,
            )
        return _finding(head, AuditStatus.suspect, "head bucket has no data now", **best_kwargs)

    recomputed = as_stored(current.value, metric, aggregate)
    drift = _drift_pct(head.value, recomputed)

    if best and best[0] != head_bucket and beats(best[1], recomputed, aggregate, metric, tolerances):
        where = "earlier" if best[0] < head_bucket else "later"
        return _finding(
            head,
            AuditStatus.bad,
            f"beaten by {where} {best[0]:%Y-%m-%d} {_fmt(best[1])} (head now {_fmt(recomputed)}, drift {drift:+.2f}%)",
            recomputed=recomputed,
            **best_kwargs,
        )

    if not eligible(current, aggregate, metric, period):
        return _finding(
            head,
            AuditStatus.suspect,
            f"head bucket no longer passes the record guard (value {_fmt(recomputed)}, {current.interval_count} intervals)",
            recomputed=recomputed,
            **best_kwargs,
        )

    if drifted(head.value, recomputed, spec.metric, tolerances):
        return _finding(
            head, AuditStatus.suspect, f"value drift {drift:+.2f}%, still rank 1", recomputed=recomputed, **best_kwargs
        )

    return _finding(head, AuditStatus.ok, "", recomputed=recomputed, **best_kwargs)


def evaluate_interval_head(
    head: ChainHead,
    spec: HeadSpec,
    recomputed: float | None,
    recomputed_prev: float | None,
    tolerances: Tolerances | None = None,
) -> HeadFinding:
    """Check an interval head: value drift, and it must still beat its predecessor in the chain."""
    tolerances = tolerances or Tolerances()

    if recomputed is None:
        return _finding(head, AuditStatus.suspect, "no data at the head interval now")

    recomputed = as_stored(recomputed, spec.metric, head.aggregate)
    drift = _drift_pct(head.value, recomputed)
    prev_value = recomputed_prev if recomputed_prev is not None else head.prev_value
    prev_kwargs: dict[str, Any] = (
        {"best_interval": head.prev_interval, "best_value": prev_value} if head.prev_interval and prev_value is not None else {}
    )

    if prev_value is not None and beats(prev_value, recomputed, head.aggregate, spec.metric, tolerances):
        when = f"{head.prev_interval:%Y-%m-%d %H:%M}" if head.prev_interval else "previous"
        return _finding(
            head,
            AuditStatus.bad,
            f"no longer beats previous record {when} {_fmt(prev_value)} (head now {_fmt(recomputed)}, drift {drift:+.2f}%)",
            recomputed=recomputed,
            **prev_kwargs,
        )

    if drifted(head.value, recomputed, spec.metric, tolerances):
        return _finding(
            head, AuditStatus.suspect, f"value drift {drift:+.2f}%, still beats previous", recomputed=recomputed, **prev_kwargs
        )

    return _finding(head, AuditStatus.ok, "", recomputed=recomputed, **prev_kwargs)


def select_heads(heads: Iterable[ChainHead], min_significance: int, networks: Sequence[str] | None = None) -> list[ChainHead]:
    """Heads to audit: significance >= min_significance, plus every month head."""
    wanted = {n.upper() for n in networks} if networks else None
    return [
        h
        for h in heads
        if (h.significance >= min_significance or h.period == MilestonePeriod.month.value)
        and (wanted is None or (h.network_id or "").upper() in wanted)
    ]


def _bucket_touched(start: datetime, period: str, since: datetime) -> bool:
    """Whether a bucket ends after `since`: a repair from `since` can have changed it."""
    try:
        p = MilestonePeriod(period)
    except ValueError:
        return start >= since
    if p == MilestonePeriod.interval or p not in AUDITED_PERIODS:
        return start >= since
    return bucket_end(bucket_start(start, p), p) > since


def filter_since(findings: Iterable[HeadFinding], since: datetime | None) -> list[HeadFinding]:
    """Keep findings a repair from `since` can have touched: the head's bucket, or the bucket beating it, ends after it.

    Bucket END, not start: a month head at 2026-10-01 holds the days of a repair from 2026-10-27.
    """
    if since is None:
        return list(findings)
    return [
        f
        for f in findings
        if _bucket_touched(f.interval, f.period, since)
        or (f.best_interval is not None and _bucket_touched(f.best_interval, f.period, since))
    ]


def summarise(findings: Iterable[HeadFinding]) -> dict[AuditStatus, int]:
    counts = dict.fromkeys(AuditStatus, 0)
    for f in findings:
        counts[f.status] += 1
    return counts


def head_audit_reminder(since: date | datetime | None) -> str:
    """The line repair scripts print at the end (#786)."""
    when = f"{since:%Y-%m-%d}" if since else "<repair start>"
    return f"run the milestone head audit: opennem milestones audit-heads --since {when}"


# --- I/O ------------------------------------------------------------------------------------------

_HEADS_QUERY = text("""
    with heads as (
        select distinct on (record_id)
            record_id, interval, instance_id, aggregate, metric, period, significance, value,
            network_id, network_region, fueltech_id, previous_instance_id
        from milestones
        order by record_id, interval desc
    )
    select
        h.record_id, h.interval, h.instance_id, h.aggregate, h.metric, h.period, h.significance, h.value,
        h.network_id, h.network_region, h.fueltech_id, p.interval as prev_interval, p.value as prev_value
    from heads h
    left join milestones p on p.instance_id = h.previous_instance_id
""")


async def load_chain_heads() -> list[ChainHead]:
    """Every chain head with its predecessor, from the milestones table. Read only."""
    from opennem.db import get_read_session

    async with get_read_session() as session:
        rows = (await session.execute(_HEADS_QUERY)).all()

    return [
        ChainHead(
            record_id=r.record_id,
            interval=r.interval,
            instance_id=r.instance_id,
            aggregate=MilestoneAggregate(r.aggregate),
            metric=r.metric,
            period=r.period,
            significance=int(r.significance or 0),
            value=float(r.value),
            network_id=r.network_id,
            network_region=r.network_region,
            fueltech_id=r.fueltech_id,
            prev_interval=r.prev_interval,
            prev_value=float(r.prev_value) if r.prev_value is not None else None,
        )
        for r in rows
    ]


def _network_ids_sql(network: NetworkSchema) -> str:
    return list_to_case([network.code.upper(), *[s.code for s in network.subnetworks or []]])


def _generation_tables(grouping: GroupingConfig) -> tuple[str, str]:
    """(daily MV, interval MV) for a generation grouping: renewable groupings have their own MVs."""
    if "renewable" in grouping.group_by_fields:
        return "renewable_intervals_daily_mv", "renewable_intervals_mv"
    return "fueltech_intervals_daily_mv", "fueltech_intervals_mv"


def build_daily_generation_query(network: NetworkSchema, metric: MilestoneType, grouping: GroupingConfig, end: datetime) -> str:
    """Daily (date, group..., value) for a generation metric, from the daily MV FINAL.

    The FINAL is deliberately unscoped by date: rank 1 needs the chain's full history. It reads the
    daily MV (one row per day/region/fueltech), not an interval table, and runs off the event loop.
    """
    daily_table, _ = _generation_tables(grouping)
    column = {MilestoneType.energy: "energy", MilestoneType.emissions: "emissions"}[metric]
    group_select = "".join(f", {f}" for f in grouping.group_by_fields)
    return f"""
    SELECT date{group_select}, sum({column}) AS value_sum
    FROM {daily_table} FINAL
    WHERE network_id IN ({_network_ids_sql(network)})
      {get_network_region_filter_sql(network)}
      AND date < toDate('{end:%Y-%m-%d}')
    GROUP BY date{group_select}
    """


def build_daily_interval_count_query(network: NetworkSchema, grouping: GroupingConfig, end: datetime) -> str:
    """Daily (date, group..., distinct intervals) from the interval MV: the backlog's low-guard count.

    The daily MV only keeps a per-row count, and neither the max of those nor the slot bitmaps give
    the distinct count across a group's rows. A distinct count needs no FINAL (superseded versions
    repeat the same interval), so this is a cheap scan of the key columns.
    """
    _, interval_table = _generation_tables(grouping)
    group_select = "".join(f", {f}" for f in grouping.group_by_fields)
    return f"""
    SELECT toDate(interval) AS day{group_select}, uniqExact(interval) AS intervals
    FROM {interval_table}
    WHERE network_id IN ({_network_ids_sql(network)})
      {get_network_region_filter_sql(network)}
      AND interval < toDateTime('{end:%Y-%m-%d} 00:00:00')
    GROUP BY day{group_select}
    """


def attach_interval_counts(
    value_rows: Iterable[Sequence[Any]], count_rows: Iterable[Sequence[Any]], fields: Sequence[str]
) -> list[tuple[date, tuple[Any, ...], float | None, int]]:
    """Join (date, group..., value) with (date, group..., count) rows into rollup_sum input."""
    n = len(fields)
    counts = {(r[0], normalise_key(fields, r[1 : 1 + n])): int(r[1 + n] or 0) for r in count_rows}
    out: list[tuple[date, tuple[Any, ...], float | None, int]] = []
    for r in value_rows:
        key = normalise_key(fields, r[1 : 1 + n])
        out.append((r[0], key, r[1 + n], counts.get((r[0], key), 0)))
    return out


def build_daily_market_query(network: NetworkSchema, grouping: GroupingConfig, end: datetime) -> str:
    """Daily demand energy and proportion inputs per group, from market_summary FINAL.

    Deliberately unscoped FINAL, like the backlog's own market queries: rank 1 needs full history,
    and market_summary is one row per (interval, region), so this is a few million rows a network.
    """
    group_select = "".join(f", {f}" for f in grouping.group_by_fields)
    regions = list_to_case(network.regions or [network.code])
    return f"""
    SELECT
        toDate(interval) AS date{group_select},
        sum(demand_energy) AS demand_energy_sum,
        count(distinct interval) AS interval_count_distinct,
        sum(generation_renewable) AS generation_renewable_sum,
        sum(demand_gross) AS demand_gross_sum,
        countIf(network_region IN ({regions}) AND demand_gross IS NOT NULL AND generation_renewable IS NOT NULL) AS complete_pairs
    FROM market_summary FINAL
    WHERE network_id IN ({_network_ids_sql(network)})
      {get_network_region_filter_sql(network)}
      AND interval < toDateTime('{end:%Y-%m-%d %H:%M:%S}')
    GROUP BY date{group_select}
    """


async def _execute(client: Any | None, query: str) -> list[tuple[Any, ...]]:
    """Run a blocking clickhouse query off the event loop. The client is made inside the thread (#703)."""

    def _run() -> list[tuple[Any, ...]]:
        if client is not None:
            return list(client.execute(query))
        from opennem.db.clickhouse import get_clickhouse_client

        rows: Any = get_clickhouse_client(timeout=60).execute(query)
        return list(rows)

    return await asyncio.to_thread(_run)


def _metric_def(metric: MilestoneType):
    for metric_def in get_metric_registry():
        if metric_def.metric == metric:
            return metric_def
    raise ValueError(f"No metric definition for {metric}")


async def _query_interval_values(
    client: Any | None, spec: HeadSpec, interval: datetime, cache: dict[tuple[Any, ...], dict[tuple[Any, ...], float | None]]
) -> float | None:
    """Recompute one interval of a head's series with the incremental path's query."""
    cache_key = (spec.network.code, spec.metric, spec.grouping.name, interval)
    if cache_key not in cache:
        query = build_period_aggregation_query(
            metric_def=_metric_def(spec.metric),
            network=spec.network,
            grouping=spec.grouping,
            period=MilestonePeriod.interval,
            period_start=interval,
            period_end=interval + timedelta(minutes=spec.network.interval_size),
        )
        fields = spec.grouping.group_by_fields
        rows = await _execute(client, query)
        cache[cache_key] = {
            normalise_key(fields, row[1 : 1 + len(fields)]): (
                float(row[1 + len(fields)]) if row[1 + len(fields)] is not None else None
            )
            for row in rows
        }
    return cache[cache_key].get(spec.key)


async def audit_heads(
    since: datetime | None = None,
    min_significance: int = DEFAULT_MIN_SIGNIFICANCE,
    networks: Sequence[str] | None = None,
    tolerances: Tolerances | None = None,
    client: Any | None = None,
    heads: Sequence[ChainHead] | None = None,
    now: dict[str, datetime] | None = None,
) -> list[HeadFinding]:
    """Audit chain heads (significance >= min_significance plus all month heads). Read only.

    Args:
        since: only report heads at/after this (naive network time), or heads beaten by a bucket at/after
            it; rank checks always use the full history
        min_significance: significance floor; month heads are always audited
        networks: network codes to audit (NEM, WEM); default both
        tolerances: value drift / rank tolerances
        client: clickhouse client (tests); default a thread-local client per query thread
        heads: chain heads (tests); default loaded from the milestones table
        now: last completed interval per network code (tests); default the wall clock

    Returns:
        findings sorted BAD, SUSPECT, OK then by record id
    """
    from opennem.utils.dates import get_last_completed_interval_for_network

    tolerances = tolerances or Tolerances()
    all_heads = list(heads) if heads is not None else await load_chain_heads()
    selected = select_heads(all_heads, min_significance, networks)

    ends = {code: (now or {}).get(code) or get_last_completed_interval_for_network(net) for code, net in _NETWORKS.items()}

    specs: list[tuple[ChainHead, HeadSpec]] = []
    for head in selected:
        spec = head_spec(head)
        if spec is None:
            logger.debug(f"head audit: skipping unsupported chain {head.record_id}")
            continue
        specs.append((head, spec))

    findings: list[HeadFinding] = []

    # day+ heads: one daily query per (network, source, grouping), rolled up per period in Python
    daily_cache: dict[tuple[Any, ...], list[tuple[Any, ...]]] = {}
    series_cache: dict[tuple[Any, ...], dict[tuple[Any, ...], dict[datetime, BucketValue]]] = {}

    for head, spec in specs:
        if spec.period == MilestonePeriod.interval:
            continue

        network, grouping, period = spec.network, spec.grouping, spec.period
        end = ends[network.code]
        fields = grouping.group_by_fields
        market = spec.metric in (MilestoneType.demand, MilestoneType.proportion)
        source = "market" if market else spec.metric.value
        daily_key = (network.code, source, grouping.name)

        if bucket_start(head.interval, period) >= bucket_start(end, period):
            # head sits in the current, incomplete bucket: nothing settled to compare yet
            continue

        if daily_key not in daily_cache:
            if market:
                daily_cache[daily_key] = await _execute(client, build_daily_market_query(network, grouping, end))
            else:
                count_key = (network.code, "counts", _generation_tables(grouping)[1], grouping.name)
                if count_key not in daily_cache:
                    daily_cache[count_key] = await _execute(client, build_daily_interval_count_query(network, grouping, end))
                values = await _execute(client, build_daily_generation_query(network, spec.metric, grouping, end))
                daily_cache[daily_key] = await asyncio.to_thread(attach_interval_counts, values, daily_cache[count_key], fields)
            logger.info(f"head audit: {network.code} {source} {grouping.name}: {len(daily_cache[daily_key])} daily rows")

        series_key = (*daily_key, spec.metric.value, period.value)
        if series_key not in series_cache:
            # pure python over the full daily history: off the loop, it held it ~1s (BACKEND-6A6/6B3)
            series_cache[series_key] = await asyncio.to_thread(
                rollup_series, daily_cache[daily_key], spec.metric, period, network, fields
            )

        findings.append(
            evaluate_period_head(head, spec, series_cache[series_key].get(spec.key), bucket_start(end, period), tolerances)
        )

    # interval heads: point recompute of the head and its predecessor
    interval_cache: dict[tuple[Any, ...], dict[tuple[Any, ...], float | None]] = {}
    for head, spec in specs:
        if spec.period != MilestonePeriod.interval:
            continue
        if head.interval > ends[spec.network.code] - timedelta(hours=INTERVAL_SETTLE_HOURS):
            continue  # rooftop may not have settled yet (#652)

        recomputed = await _query_interval_values(client, spec, head.interval, interval_cache)
        recomputed_prev = (
            await _query_interval_values(client, spec, head.prev_interval, interval_cache) if head.prev_interval else None
        )
        findings.append(evaluate_interval_head(head, spec, recomputed, recomputed_prev, tolerances))

    findings = filter_since(findings, since)
    order = {AuditStatus.bad: 0, AuditStatus.suspect: 1, AuditStatus.ok: 2}
    findings.sort(key=lambda f: (order[f.status], f.record_id))

    counts = summarise(findings)
    logger.info(
        f"head audit: {len(findings)} heads checked, BAD {counts[AuditStatus.bad]} "
        f"SUSPECT {counts[AuditStatus.suspect]} OK {counts[AuditStatus.ok]}"
    )
    return findings


__all__ = [
    "AuditStatus",
    "BucketValue",
    "ChainHead",
    "HeadFinding",
    "HeadSpec",
    "Tolerances",
    "audit_heads",
    "evaluate_interval_head",
    "evaluate_period_head",
    "head_audit_reminder",
    "head_spec",
    "rollup_proportion",
    "rollup_series",
    "rollup_sum",
]
