"""
Incremental milestone record detection.

Loads current state (latest high/low per record_id), queries only the latest completed
periods from ClickHouse, compares against current records, and INSERTs only new records.

Replaces the full-regeneration approach in backlog.py for scheduled runs.
"""

import logging
import uuid
from datetime import datetime, timedelta

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db.clickhouse import get_clickhouse_client
from opennem.recordreactor.buckets import get_period_start_end
from opennem.recordreactor.metric_registry import (
    GroupingConfig,
    MetricDefinition,
    get_metric_definitions_for_period,
    row_contains_rooftop,
)
from opennem.recordreactor.persistence import check_and_persist_milestones_chunked
from opennem.recordreactor.queries_incremental import get_last_settled_interval, query_all_groupings_for_period
from opennem.recordreactor.rebuild_guard import skip_if_rebuild_in_progress
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestonePeriod,
    MilestoneRecordOutputSchema,
    MilestoneRecordSchema,
    MilestoneType,
)
from opennem.recordreactor.state import refresh_current_milestone_state, update_milestone_state
from opennem.recordreactor.unit import get_milestone_unit
from opennem.recordreactor.utils import check_milestone_is_new, should_notify_milestone
from opennem.recordreactor.watermark import (
    get_gap_backfill_enqueued_at,
    get_last_incremental_run,
    get_last_settled_intervals,
    set_gap_backfill_enqueued_at,
    set_last_incremental_run,
)
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.tasks.broker import get_redis_pool
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.recordreactor.incremental")

_DEFAULT_NETWORKS = [NetworkNEM, NetworkWEM]

# Fixed arq job id so only one gap backfill is ever queued or running
GAP_BACKFILL_JOB_ID = "milestone_gap_backfill"

# Our own floor on how often a backfill may be queued, independent of arq's job id. A pass that
# fails before it updates the watermark leaves the detector permanently stale, and this is what
# stops that becoming continuous background load (#658).
GAP_BACKFILL_COOLDOWN = timedelta(hours=1)

# Cap social submissions per run so a day-boundary burst doesn't flood the approval
# queue. Most significant first; anything dropped is logged (not silent).
_MAX_SOCIAL_POSTS_PER_RUN = 10

_DEFAULT_PERIODS = [
    MilestonePeriod.interval,
    MilestonePeriod.day,
    MilestonePeriod.month,
    MilestonePeriod.quarter,
    MilestonePeriod.year,
]


def _get_last_completed_quarter(dt: datetime) -> tuple[datetime, datetime]:
    """Return (start, end) of the last fully completed quarter.

    Quarter boundaries: Jan 1, Apr 1, Jul 1, Oct 1.
    If dt is May 15, current quarter started Apr 1, so last completed = Jan 1 to Apr 1.
    If dt is Jan 15, current quarter started Jan 1, so last completed = Oct 1 (prev year) to Jan 1.
    """
    current_q_month = ((dt.month - 1) // 3) * 3 + 1
    current_q_start = dt.replace(month=current_q_month, day=1, hour=0, minute=0, second=0, microsecond=0)

    end = current_q_start
    if current_q_month == 1:
        start = end.replace(year=end.year - 1, month=10)
    else:
        start = end.replace(month=current_q_month - 3)

    return start, end


def _get_last_completed_year(dt: datetime) -> tuple[datetime, datetime]:
    """Return (start, end) of the last fully completed calendar year."""
    start_of_year = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_of_year.replace(year=start_of_year.year - 1), start_of_year


def get_interval_window_start(
    settled_interval: datetime,
    last_settled_interval: datetime | None,
    lookback_minutes: int,
    max_catchup_hours: int,
) -> datetime:
    """Where the interval window starts: from the last settled interval this checker covered.

    A fixed lookback before the current settled interval skips intervals whenever the settled
    interval jumps further than the lookback between two runs — a worker restart, a slow rooftop
    crawl, rooftop landing in a batch. Those intervals were then never checked with rooftop in
    them (dev missed QLD1 renewables at 8,360.7 MW on 2026-09-22 12:30, #662). So the window
    reaches back to `last_settled_interval`, the watermark of what earlier passes covered, when
    that is older than the lookback.

    The reach back is capped at `max_catchup_hours` before the settled interval so a stale
    watermark (days of downtime) can't turn a 5-minute cron into a full scan; the gap backfill
    covers anything older. No watermark (first run after deploy) falls back to the lookback.
    """
    start = settled_interval - timedelta(minutes=lookback_minutes)

    if last_settled_interval is not None and last_settled_interval < start:
        start = last_settled_interval

    return max(start, settled_interval - timedelta(hours=max_catchup_hours))


def get_completed_periods(
    now: datetime,
    network: NetworkSchema,
    settled_interval: datetime | None = None,
    interval_lookback_minutes: int = 0,
    last_settled_interval: datetime | None = None,
    max_catchup_hours: int = 24,
) -> list[tuple[MilestonePeriod, datetime, datetime]]:
    """Return the most recently completed period for each period level.

    Always checks all period levels — the comparison against state ensures
    we only INSERT a record once (idempotent). This avoids missing records
    if the checker doesn't run exactly at a period boundary.

    Quarter and year use aligned boundaries to avoid inserting partial-period
    records (e.g., a mid-quarter run must not create a partial quarter milestone).

    The interval period spans `interval_lookback_minutes` before `settled_interval` through the
    last completed interval. It reaches back because rooftop lands in 30-minute blocks, so the
    settled interval jumps several intervals at a time and a single-interval query would skip the
    rest; it still runs up to `now` because only the rooftop-dependent rows are held back, and
    that is decided per row in `_map_row_to_records` (#652). Re-checking already-recorded
    intervals is idempotent — `check_milestone_is_new` requires the interval to advance.
    Day+ periods are not gated on settledness.

    When `last_settled_interval` (the watermark of what earlier passes covered) is older than the
    lookback, the window starts there instead, up to `max_catchup_hours` back (#662). See
    `get_interval_window_start`.

    Returns list of (period, period_start, period_end) tuples.
    """
    completed: list[tuple[MilestonePeriod, datetime, datetime]] = []

    for period in _DEFAULT_PERIODS:
        if period == MilestonePeriod.quarter:
            start, end = _get_last_completed_quarter(now)
        elif period == MilestonePeriod.year:
            start, end = _get_last_completed_year(now)
        elif period == MilestonePeriod.interval and settled_interval is not None:
            window_start = get_interval_window_start(
                settled_interval,
                last_settled_interval,
                lookback_minutes=interval_lookback_minutes,
                max_catchup_hours=max_catchup_hours,
            )
            start, _ = get_period_start_end(window_start, period, network)
            _, end = get_period_start_end(now, period, network)
        else:
            start, end = get_period_start_end(now, period, network)
        completed.append((period, start, end))

    return completed


def _map_row_to_records(
    row: dict,
    metric_def: MetricDefinition,
    grouping: GroupingConfig,
    period: MilestonePeriod,
    network: NetworkSchema,
    current_state: dict[str, MilestoneRecordOutputSchema],
    settled_interval: datetime | None = None,
    unseeded_record_ids: set[str] | None = None,
) -> list[MilestoneRecordSchema]:
    """Convert a single aggregated row into milestone record schemas for both high and low.

    Compares against current state and only returns records that are new. Every genuine new
    extreme is returned for persistence — whether it is announced is decided separately by
    `_select_notifiable_instance_ids` (#651).

    At the interval period a row whose value can contain rooftop solar is dropped until the
    interval has settled (#652). The test is per row, not per query: one fueltech query returns
    solar alongside coal, and one renewable query returns renewables alongside fossils, so gating
    the query would hold back series that have no rooftop in them at all.

    A record_id with no chain is skipped rather than seeded from the one value in front of us, and
    collected into `unseeded_record_ids` for the caller to report (#656).
    """
    value = row.get("value")
    if value is None:
        return []

    import datetime as dt

    interval_count = row.get("interval_count", 1)
    raw_interval = row["time_bucket"]
    # ClickHouse returns datetime.date for day+ buckets — normalize to datetime
    if isinstance(raw_interval, dt.date) and not isinstance(raw_interval, datetime):
        interval = datetime.combine(raw_interval, datetime.min.time())
    else:
        interval = raw_interval

    # Hold back rows that are still waiting on rooftop; everything else runs to the last
    # completed interval
    if (
        period == MilestonePeriod.interval
        and settled_interval is not None
        and interval > settled_interval
        and row_contains_rooftop(metric_def, grouping, row)
    ):
        return []

    # Determine network_region and fueltech from grouping fields
    network_region = row.get("network_region") if "network_region" in grouping.group_by_fields else None
    fueltech: MilestoneFueltechGrouping | None = None

    if "fueltech_group_id" in grouping.group_by_fields:
        fueltech_val = row.get("fueltech_group_id")
        if fueltech_val not in MilestoneFueltechGrouping.__members__:
            return []  # skip unknown fueltechs (e.g., bidirectional battery)
        fueltech = MilestoneFueltechGrouping(fueltech_val)
    elif "renewable" in grouping.group_by_fields:
        renewable_val = row.get("renewable")
        fueltech = MilestoneFueltechGrouping.renewables if renewable_val else MilestoneFueltechGrouping.fossils

    # Apply fueltech date cutoffs
    if fueltech and fueltech.value in metric_def.fueltech_date_cutoffs:
        cutoff = metric_def.fueltech_date_cutoffs[fueltech.value]
        if interval < cutoff:
            return []

    # Handle demand special case: demand records use fueltech=demand and
    # output metric is energy (day+) or power (interval)
    metric_out = metric_def.metric
    if metric_def.metric == MilestoneType.demand:
        fueltech = MilestoneFueltechGrouping.demand
        metric_out = MilestoneType.power if period == MilestonePeriod.interval else MilestoneType.energy

    unit = get_milestone_unit(metric_out)

    # Filter by min_value for HIGH records
    rounded_value = round(value, metric_def.round_to)

    # Check interval threshold for LOW records
    threshold = metric_def.interval_thresholds.get(period, 1)

    records: list[MilestoneRecordSchema] = []

    for aggregate in [MilestoneAggregate.high, MilestoneAggregate.low]:
        # Build a candidate record to compute its record_id
        candidate = MilestoneRecordSchema(
            interval=interval,
            aggregate=aggregate,
            metric=metric_out,
            period=period,
            network=network,
            unit=unit,
            network_region=network_region,
            fueltech=fueltech,
            value=rounded_value,
            instance_id=uuid.uuid4(),
        )

        record_id = candidate.record_id

        # For HIGH: skip if value is below min_value floor
        if aggregate == MilestoneAggregate.high and rounded_value <= metric_def.min_value:
            continue

        # For LOW: skip if value is 0 or negative (unless allow_negative) or interval count too low
        if aggregate == MilestoneAggregate.low:
            if not metric_def.allow_negative and value <= 0:
                continue
            if interval_count < threshold:
                continue

        # Compare against current state
        prev = current_state.get(record_id)

        # An empty chain is not evidence that this value is an all-time extreme — it means nothing
        # has established the extreme yet. Minting a record here wrote wem solar's *highest* day
        # of the week as its all-time low (#656). The backlog builds the chain from history; this
        # path only ever extends one. A genuinely new series therefore waits for the next backlog
        # run (monthly reconciliation, or one kicked off after the warning the caller logs).
        if prev is None:
            if unseeded_record_ids is not None:
                unseeded_record_ids.add(record_id)
            logger.debug(f"Skipping {record_id} at {interval}: no chain to compare against")
            continue

        if not check_milestone_is_new(candidate, prev):
            continue

        # Set previous_instance_id for chain linking
        candidate.previous_instance_id = prev.instance_id

        # Calculate pct_change
        if prev.value and prev.value != 0:
            pct = ((value - prev.value) / abs(prev.value)) * 100
            if abs(pct) < 9999 and abs(pct) > 0.01:
                candidate.pct_change = round(pct, 2)

        records.append(candidate)

    return records


def _select_notifiable_instance_ids(
    records: list[MilestoneRecordSchema],
    current_state: dict[str, MilestoneRecordOutputSchema],
    debounce_intervals: int,
) -> set[uuid.UUID]:
    """Pick the records that should raise an outbound notification.

    Every record passed in is persisted — the debounce only decides what gets announced (#651).
    The anchor is the last record announced for that record_id (falling back to the current stored
    record), so a value that breaks its own record every interval is announced once per window
    rather than once per interval.
    """
    if debounce_intervals <= 0:
        return {r.instance_id for r in records if r.instance_id}

    notifiable: set[uuid.UUID] = set()
    anchors: dict[str, MilestoneRecordOutputSchema | MilestoneRecordSchema] = {}

    for record in sorted(records, key=lambda r: r.interval):
        anchor = anchors.get(record.record_id) or current_state.get(record.record_id)

        if not should_notify_milestone(record, anchor, debounce_intervals=debounce_intervals):
            continue

        if record.instance_id:
            notifiable.add(record.instance_id)

        anchors[record.record_id] = record

    return notifiable


async def _milestones_table_is_empty() -> bool:
    """An empty table needs a full rebuild, not a gap backfill."""
    from sqlalchemy import func, select

    from opennem.db import get_read_session
    from opennem.db.models.opennem import Milestones

    async with get_read_session() as session:
        result = await session.execute(select(func.max(Milestones.interval)))

    return result.scalar() is None


async def _get_downtime_hours() -> tuple[datetime | None, datetime, float]:
    """(watermark, last completed interval, hours since the checker last completed a pass).

    Staleness is measured against the watermark, not against `max(milestones.interval)`. The
    backfill covers worker downtime, and a healthy system routinely goes more than a day without
    setting a record — so measuring the newest record meant the gap never closed and the backfill
    re-enqueued itself every 15 minutes forever (#658).
    """
    now = get_last_completed_interval_for_network(NetworkNEM)
    watermark = await get_last_incremental_run()

    if watermark is None:
        return None, now, 0.0

    return watermark, now, (now - watermark).total_seconds() / 3600


async def _enqueue_gap_backfill_if_needed() -> None:
    """Queue a gap backfill job when the incremental checker has not completed a pass recently.

    The checker only looks at the latest period, so records set during an outage are never
    detected; the backlog's window functions find every record-breaking bucket in the range.

    This is enqueued rather than run inline. Since #654 a bounded backlog run seeds its running
    extremes from full history, so a gap backfill is ~8 minutes of ClickHouse work — far past the
    300s budget of the 5-minute `task_update_milestones` cron that calls this. Running it inline
    got the task killed mid-backfill, which left the gap open, which started it again on the next
    tick. The job carries the worker's default timeout instead, and the incremental pass gets on
    with its own work in the meantime.

    Two guards keep one backfill in flight. `GAP_BACKFILL_JOB_ID` is arq's: it refuses a second
    job while that id is live. `GAP_BACKFILL_COOLDOWN` is ours, in the same durable row as the
    watermark, because a pass that fails before it can update the watermark would otherwise
    re-enqueue as fast as arq allows.
    """
    if await _milestones_table_is_empty():
        logger.warning("No milestones found — run full backlog first")
        return

    watermark, now, downtime_hours = await _get_downtime_hours()

    if watermark is None:
        # Fresh deployment or a restored database: no evidence of downtime, and the pass about to
        # run writes the watermark, so the next run has something to measure against.
        logger.info("No incremental watermark yet — skipping the gap check until this run records one")
        return

    if downtime_hours <= settings.milestone_gap_backfill_threshold_hours:
        return

    enqueued_at = await get_gap_backfill_enqueued_at()

    if enqueued_at and (now - enqueued_at) < GAP_BACKFILL_COOLDOWN:
        logger.info(f"Incremental checker {downtime_hours:.0f}h stale but a backfill was queued at {enqueued_at} — waiting")
        return

    try:
        redis = await get_redis_pool()
        try:
            job = await redis.enqueue_job("task_milestone_gap_backfill", _job_id=GAP_BACKFILL_JOB_ID)
        finally:
            await redis.close()
    except Exception as e:
        logger.error(f"Could not enqueue milestone gap backfill: {e}")
        return

    await set_gap_backfill_enqueued_at(now)

    if job is None:
        logger.info(f"Incremental checker {downtime_hours:.0f}h stale — backfill already queued or recently run")
    else:
        logger.info(
            f"Incremental checker last completed a pass at {watermark}, {downtime_hours:.0f}h before {now}. "
            "Enqueued gap backfill."
        )


async def run_gap_backfill() -> None:
    """Fill the window the incremental checker missed while it was down.

    Runs as its own arq job (`task_milestone_gap_backfill`) on the worker's default job timeout,
    not inside the 5-minute incremental cron. Stands down during a rebuild for the same reason the
    incremental check does: mid-rebuild the chains are partly empty, so this would insert records
    the finished rebuild would never have produced (#640).
    """
    from opennem.recordreactor.backlog import run_milestone_analysis

    if await skip_if_rebuild_in_progress("milestone gap backfill"):
        return

    if await _milestones_table_is_empty():
        logger.warning("No milestones found — run full backlog first")
        return

    watermark, now, downtime_hours = await _get_downtime_hours()

    if watermark is None:
        logger.info("No incremental watermark — nothing to measure a gap against")
        return

    if downtime_hours <= settings.milestone_gap_backfill_threshold_hours:
        logger.info(f"Incremental checker is {downtime_hours:.0f}h stale — caught up before the backfill ran")
        return

    logger.info(f"Filling the {downtime_hours:.0f}h the incremental checker missed ({watermark} to {now})")

    # Align to start of day so day-period queries get complete days
    start_date = watermark.replace(hour=0, minute=0, second=0, microsecond=0)
    await run_milestone_analysis(start_date=start_date, end_date=now)

    logger.info("Gap backfill complete")


async def run_incremental_milestone_check(
    networks: list[NetworkSchema] | None = None,
    alert_slack: bool = True,
) -> list[MilestoneRecordOutputSchema]:
    """Run incremental milestone detection.

    0. Stand down entirely if a full rebuild is running
    1. Enqueue a gap backfill job if this checker hasn't completed a pass recently
    2. Load current state (latest high/low per record_id)
    3. Determine which periods have just completed (interval stops at the last settled interval)
    4. Query ClickHouse for aggregated values
    5. Compare against current records
    6. INSERT new records
    7. Record the watermark, then alert on significance >= 9

    Step 0 covers the gap backfill as well as the check itself: nothing is enqueued during a
    rebuild, and the job stands down again when it runs. Mid-rebuild the milestones table is empty
    or partly refilled, so both paths would read no current record for a record_id and mint the
    first bucket they see as a brand new one (#640).
    """
    if await skip_if_rebuild_in_progress("incremental milestone check"):
        return []

    # Hand any downtime gap to its own job — it is minutes of work, this cron has 300s (#654)
    await _enqueue_gap_backfill_if_needed()

    client = get_clickhouse_client()
    # Always reload state from DB to avoid stale reads after reconciliation/admin writes
    current_state = await refresh_current_milestone_state()
    all_new_records: list[MilestoneRecordOutputSchema] = []
    # records that clear the notification debounce — the record itself is always persisted (#651)
    notifiable_instance_ids: set[uuid.UUID] = set()
    # record_ids with data but no chain — reported at the end of the run (#656)
    unseeded_record_ids: set[str] = set()
    # the settled interval each network's pass covers, written to the watermark at the end (#662)
    covered_settled_intervals: dict[str, datetime] = {}
    last_settled_intervals = await get_last_settled_intervals()

    for network in networks or _DEFAULT_NETWORKS:
        # get_last_completed_interval_for_network returns the start of the current interval
        # (e.g. 10:05 at 10:07) — subtract one interval to get the last truly completed one
        now = get_last_completed_interval_for_network(network) - timedelta(minutes=network.interval_size)
        settled_interval = get_last_settled_interval(client=client, network=network, now=now)
        completed_periods = get_completed_periods(
            now,
            network,
            settled_interval=settled_interval,
            interval_lookback_minutes=settings.milestone_interval_settle_lag_minutes,
            last_settled_interval=last_settled_intervals.get(network.code),
            max_catchup_hours=settings.milestone_interval_max_catchup_hours,
        )
        covered_settled_intervals[network.code] = settled_interval

        logger.info(f"Checking {network.code}: {len(completed_periods)} periods at {now} (settled at {settled_interval})")

        for period, period_start, period_end in completed_periods:
            # Get all metric definitions valid for this period
            metric_defs = get_metric_definitions_for_period(period)

            for metric_def in metric_defs:
                # Query all groupings for this metric + period
                grouping_results = query_all_groupings_for_period(
                    client=client,
                    metric_def=metric_def,
                    network=network,
                    period=period,
                    period_start=period_start,
                    period_end=period_end,
                )

                # Collect new records from all groupings
                new_records: list[MilestoneRecordSchema] = []

                for grouping, rows in grouping_results:
                    for row in rows:
                        records = _map_row_to_records(
                            row=row,
                            metric_def=metric_def,
                            grouping=grouping,
                            period=period,
                            network=network,
                            current_state=current_state,
                            settled_interval=settled_interval,
                            unseeded_record_ids=unseeded_record_ids,
                        )
                        new_records.extend(records)

                if new_records:
                    notifiable_instance_ids |= _select_notifiable_instance_ids(
                        new_records,
                        current_state,
                        debounce_intervals=settings.milestone_interval_debounce_intervals,
                    )

                    logger.info(
                        f"Found {len(new_records)} new records for {network.code} {metric_def.metric.value} {period.value}"
                    )

                    # Persist new records
                    persisted = await check_and_persist_milestones_chunked(new_records)
                    all_new_records.extend(persisted)

                    # Update in-memory state for subsequent comparisons
                    for record in persisted:
                        update_milestone_state(record.record_id, record)

    # The pass completed: this is what the gap detector measures downtime against (#658). Written
    # before the alerting below so a Slack or social failure can't make the checker look stale.
    # The settled intervals go in the same upsert, and only after every record above is persisted:
    # a pass that dies part way leaves them where they were, so the next pass re-covers the gap
    # (#662).
    await set_last_incremental_run(
        get_last_completed_interval_for_network(NetworkNEM),
        settled_intervals=covered_settled_intervals,
    )

    if unseeded_record_ids:
        sample = ", ".join(sorted(unseeded_record_ids)[:5])
        logger.warning(
            f"{len(unseeded_record_ids)} record ids have data but no chain to compare against and were skipped "
            f"(e.g. {sample}) — run the backlog to build them"
        )

    # Alert on high-significance records. The interval debounce gates the announcement only:
    # a record inside the window is stored above but not announced here (#651).
    significant_records = [r for r in all_new_records if r.significance >= 9]
    announce_records = [r for r in significant_records if r.instance_id in notifiable_instance_ids]

    if alert_slack and announce_records and settings.slack_hook_records:
        descriptions = [f"- {r.description} ({r.value})" for r in announce_records[:10]]
        message = f"New milestone records detected ({len(announce_records)}):\n" + "\n".join(descriptions)
        await slack_message(
            webhook_url=settings.slack_hook_records,
            message=message,
        )

    # Submit significant milestones to social media pipeline
    if announce_records:
        import asyncio as _asyncio

        from sqlalchemy import and_, select

        from opennem.db import get_read_session
        from opennem.db.models.opennem import Milestones
        from opennem.social.content import build_record_url, render_milestone_card, render_milestone_social_text
        from opennem.social.pipeline import create_social_post
        from opennem.social.schema import CreateSocialPostRequest, SocialPostType

        # Most significant first; cap the per-run burst and log anything dropped.
        ordered = sorted(announce_records, key=lambda r: r.significance, reverse=True)
        to_post = ordered[:_MAX_SOCIAL_POSTS_PER_RUN]
        if len(ordered) > _MAX_SOCIAL_POSTS_PER_RUN:
            logger.warning(
                f"Capping social submissions at {_MAX_SOCIAL_POSTS_PER_RUN}; "
                f"dropping {len(ordered) - _MAX_SOCIAL_POSTS_PER_RUN} lower-significance records"
            )

        for record in to_post:
            # Isolate each record so one render/upload failure doesn't drop the batch.
            try:
                text = render_milestone_social_text(record)

                # Fetch the most recent 40 history records for the sparkline.
                # Order desc + limit so the sparkline reflects the recent trend;
                # then reverse so the renderer gets oldest-→-newest input.
                async with get_read_session() as session:
                    rows = (
                        (
                            await session.execute(
                                select(Milestones)
                                .where(and_(Milestones.record_id == record.record_id, Milestones.interval < record.interval))
                                .order_by(Milestones.interval.desc())
                                .limit(40)
                            )
                        )
                        .scalars()
                        .all()
                    )
                history = [(r.interval, float(r.value)) for r in reversed(rows)]

                # Render card image (run in thread — html2image is sync + slow)
                image_bytes = await _asyncio.to_thread(
                    render_milestone_card,
                    record_id=record.record_id,
                    interval=record.interval,
                    description=record.description,
                    value=float(record.value),
                    value_unit=record.value_unit or "",
                    pct_change=float(record.pct_change) if record.pct_change is not None else None,
                    period=record.period,
                    network_region=record.network_region,
                    fueltech_id=record.fueltech_id,
                    history=history,
                )

                focus_ts_ms = int(record.interval.timestamp() * 1000)
                link_url = build_record_url(record.record_id, focus_ts_ms)

                await create_social_post(
                    CreateSocialPostRequest(
                        post_type=SocialPostType.MILESTONE,
                        text_content=text,
                        source_type="recordreactor",
                        source_id=str(record.instance_id),
                        network_id=record.network_id,
                        link_url=link_url,
                        metadata={
                            "fueltech_id": record.fueltech_id,
                            "significance": record.significance,
                            "aggregate": record.aggregate,
                            "record_id": record.record_id,
                        },
                    ),
                    image=image_bytes,
                )
            except Exception as e:
                logger.error(f"Failed to submit milestone {record.record_id} to social pipeline: {e}")

    if all_new_records:
        logger.info(
            f"Incremental check complete: {len(all_new_records)} new records "
            f"({len(significant_records)} significant, {len(announce_records)} announced)"
        )
    else:
        logger.debug("Incremental check complete: no new records")

    return all_new_records


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_incremental_milestone_check(alert_slack=False))
