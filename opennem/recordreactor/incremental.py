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
)
from opennem.recordreactor.persistence import check_and_persist_milestones_chunked
from opennem.recordreactor.queries_incremental import query_all_groupings_for_period
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
from opennem.recordreactor.utils import check_milestone_is_new
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.recordreactor.incremental")

_DEFAULT_NETWORKS = [NetworkNEM, NetworkWEM]

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


def get_completed_periods(now: datetime, network: NetworkSchema) -> list[tuple[MilestonePeriod, datetime, datetime]]:
    """Return the most recently completed period for each period level.

    Always checks all period levels — the comparison against state ensures
    we only INSERT a record once (idempotent). This avoids missing records
    if the checker doesn't run exactly at a period boundary.

    Quarter and year use aligned boundaries to avoid inserting partial-period
    records (e.g., a mid-quarter run must not create a partial quarter milestone).

    Returns list of (period, period_start, period_end) tuples.
    """
    completed: list[tuple[MilestonePeriod, datetime, datetime]] = []

    for period in _DEFAULT_PERIODS:
        if period == MilestonePeriod.quarter:
            start, end = _get_last_completed_quarter(now)
        elif period == MilestonePeriod.year:
            start, end = _get_last_completed_year(now)
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
) -> list[MilestoneRecordSchema]:
    """Convert a single aggregated row into milestone record schemas for both high and low.

    Compares against current state and only returns records that are new.
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

        if prev is not None:
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


async def _backfill_gap_if_needed() -> None:
    """Check if there's a gap between last milestone and now. If > 1 day, run backlog to fill it.

    This handles scenarios where the system was down for days — the incremental checker
    only looks at the latest period, so it would miss records from the gap. The backlog
    uses window functions and correctly detects every record-breaking day in the range.
    """
    from sqlalchemy import func, select

    from opennem.db import get_read_session
    from opennem.db.models.opennem import Milestones
    from opennem.recordreactor.backlog import run_milestone_analysis

    async with get_read_session() as session:
        result = await session.execute(select(func.max(Milestones.interval)))
        last_milestone = result.scalar()

    if not last_milestone:
        logger.warning("No milestones found — run full backlog first")
        return

    now = get_last_completed_interval_for_network(NetworkNEM)
    gap = now - last_milestone
    gap_hours = gap.total_seconds() / 3600

    if gap_hours > 24:
        logger.info(f"Milestone gap detected: {gap_hours:.0f}h ({last_milestone} to {now}). Running backlog to fill.")
        await run_milestone_analysis(start_date=last_milestone, end_date=now)
        logger.info("Gap backfill complete")


async def run_incremental_milestone_check(
    networks: list[NetworkSchema] | None = None,
    alert_slack: bool = True,
) -> list[MilestoneRecordOutputSchema]:
    """Run incremental milestone detection.

    1. Check for gaps > 1 day and backfill if needed
    2. Load current state (latest high/low per record_id)
    3. Determine which periods have just completed
    4. Query ClickHouse for aggregated values
    5. Compare against current records
    6. INSERT new records
    7. Alert on significance >= 9
    """
    # Fill any gap from downtime before doing the incremental check
    await _backfill_gap_if_needed()

    client = get_clickhouse_client()
    # Always reload state from DB to avoid stale reads after reconciliation/admin writes
    current_state = await refresh_current_milestone_state()
    all_new_records: list[MilestoneRecordOutputSchema] = []

    for network in networks or _DEFAULT_NETWORKS:
        # get_last_completed_interval_for_network returns the start of the current interval
        # (e.g. 10:05 at 10:07) — subtract one interval to get the last truly completed one
        now = get_last_completed_interval_for_network(network) - timedelta(minutes=network.interval_size)
        completed_periods = get_completed_periods(now, network)

        logger.info(f"Checking {network.code}: {len(completed_periods)} periods at {now}")

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
                        )
                        new_records.extend(records)

                if new_records:
                    logger.info(
                        f"Found {len(new_records)} new records for {network.code} {metric_def.metric.value} {period.value}"
                    )

                    # Persist new records
                    persisted = await check_and_persist_milestones_chunked(new_records)
                    all_new_records.extend(persisted)

                    # Update in-memory state for subsequent comparisons
                    for record in persisted:
                        update_milestone_state(record.record_id, record)

    # Alert on high-significance records
    significant_records = [r for r in all_new_records if r.significance >= 9]

    if alert_slack and significant_records and settings.slack_hook_records:
        descriptions = [f"- {r.description} ({r.value})" for r in significant_records[:10]]
        message = f"New milestone records detected ({len(significant_records)}):\n" + "\n".join(descriptions)
        await slack_message(
            webhook_url=settings.slack_hook_records,
            message=message,
        )

    # Submit significant milestones to social media pipeline
    if significant_records:
        try:
            from opennem.social.content import render_milestone_social_text
            from opennem.social.pipeline import create_social_post
            from opennem.social.schema import CreateSocialPostRequest, SocialPostType

            for record in significant_records[:5]:
                text = render_milestone_social_text(record)
                await create_social_post(
                    CreateSocialPostRequest(
                        post_type=SocialPostType.MILESTONE,
                        text_content=text,
                        source_type="recordreactor",
                        source_id=str(record.instance_id),
                        network_id=record.network_id,
                        metadata={
                            "fueltech_id": record.fueltech_id,
                            "significance": record.significance,
                            "aggregate": record.aggregate,
                            "record_id": record.record_id,
                        },
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to submit milestones to social pipeline: {e}")

    if all_new_records:
        logger.info(f"Incremental check complete: {len(all_new_records)} new records ({len(significant_records)} significant)")
    else:
        logger.debug("Incremental check complete: no new records")

    return all_new_records


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_incremental_milestone_check(alert_slack=False))
