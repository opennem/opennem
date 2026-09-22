"""Regression guard for #651: the interval debounce must gate the notification, not the record.

`check_milestone_is_new` used to return False for an extreme that landed inside the debounce
window, so the record was never stored. The stored chain was decimated — the first value in each
50-minute window was kept and the actual peak thrown away — and a later, lower value then beat the
decimated chain and published as an all-time record.

`_map_row_to_records` now returns every genuine new extreme for persistence and
`_select_notifiable_instance_ids` decides, separately, which of them the Slack/social gate
announces.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from opennem import settings
from opennem.recordreactor.incremental import _map_row_to_records, _select_notifiable_instance_ids
from opennem.recordreactor.metric_registry import GROUPING_NETWORK, get_metric_definitions_for_period
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestonePeriod,
    MilestoneRecordOutputSchema,
    MilestoneType,
)
from opennem.schema.network import NetworkNEM

POWER_METRIC = next(m for m in get_metric_definitions_for_period(MilestonePeriod.interval) if m.metric == MilestoneType.power)


def _prev(record_id: str, value: float, interval: datetime, aggregate: str = "high") -> MilestoneRecordOutputSchema:
    return MilestoneRecordOutputSchema(
        record_id=record_id,
        interval=interval,
        instance_id=uuid.uuid4(),
        aggregate=aggregate,
        metric="power",
        period="interval",
        significance=10,
        value=value,
        value_unit="MW",
        network_id="NEM",
    )


def _state(high_value: float, low_value: float, interval: datetime) -> dict[str, MilestoneRecordOutputSchema]:
    """Seed both chains so only the aggregate under test can produce a candidate."""
    return {
        "au.nem.power.interval.high": _prev("au.nem.power.interval.high", high_value, interval),
        "au.nem.power.interval.low": _prev("au.nem.power.interval.low", low_value, interval, aggregate="low"),
    }


def _map(value: float, interval: datetime, state: dict[str, MilestoneRecordOutputSchema]):
    return _map_row_to_records(
        row={"time_bucket": interval, "value": value, "interval_count": 1},
        metric_def=POWER_METRIC,
        grouping=GROUPING_NETWORK,
        period=MilestonePeriod.interval,
        network=NetworkNEM,
        current_state=state,
    )


def _map_and_notify(value: float, interval: datetime, state: dict[str, MilestoneRecordOutputSchema]):
    """Return (highs, notifiable_instance_ids) for a single aggregated row."""
    records = _map(value, interval, state)
    notifiable = _select_notifiable_instance_ids(
        records, state, debounce_intervals=settings.milestone_interval_debounce_intervals
    )
    return [r for r in records if r.aggregate == MilestoneAggregate.high], notifiable


def test_record_inside_debounce_window_is_kept_but_not_notified(monkeypatch) -> None:
    """The true peak one interval later is still a record — it just isn't announced."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 10)

    state = _state(high_value=23814.0, low_value=1.0, interval=datetime(2026, 9, 18, 12, 0))
    highs, notifiable = _map_and_notify(24020.0, datetime(2026, 9, 18, 12, 15), state)

    assert len(highs) == 1
    assert highs[0].value == 24020.0
    assert highs[0].instance_id not in notifiable


def test_record_outside_debounce_window_is_notified(monkeypatch) -> None:
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 10)

    state = _state(high_value=23814.0, low_value=1.0, interval=datetime(2026, 9, 18, 12, 0))
    highs, notifiable = _map_and_notify(24020.0, datetime(2026, 9, 18, 13, 0), state)

    assert len(highs) == 1
    assert highs[0].instance_id in notifiable


def test_first_record_in_a_chain_is_notified(monkeypatch) -> None:
    """No previous record — nothing to debounce against."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 10)

    records = _map(24020.0, datetime(2026, 9, 18, 12, 15), {})
    notifiable = _select_notifiable_instance_ids(records, {}, debounce_intervals=10)

    assert records
    assert {r.instance_id for r in records} == notifiable


@pytest.mark.parametrize("debounce", [0, 10])
def test_every_extreme_is_returned_for_persistence(monkeypatch, debounce: int) -> None:
    """A ramp across consecutive intervals yields a record every interval, debounce or not."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", debounce)

    base = datetime(2026, 9, 18, 12, 0)
    state = _state(high_value=23000.0, low_value=1.0, interval=base)

    values = [23100.0, 23500.0, 24020.0]
    for offset, value in enumerate(values, start=1):
        highs, _ = _map_and_notify(value, base.replace(minute=5 * offset), state)
        assert len(highs) == 1, f"extreme {value} was dropped instead of persisted"
        # state is not advanced here: each candidate is compared against the same seed, which is
        # exactly what the persistence layer re-anchors per batch


def test_notification_anchor_re_anchors_within_a_batch(monkeypatch) -> None:
    """A multi-interval batch announces once per window, not once per record."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 10)

    base = datetime(2026, 9, 18, 12, 0)
    state = _state(high_value=23000.0, low_value=1.0, interval=base)

    # a 12-interval ramp landing in one batch (12:05 .. 13:00), each a new high
    records = []
    for step in range(1, 13):
        records.extend(_map(23000.0 + step * 50, base + timedelta(minutes=5 * step), state))

    highs = [r for r in records if r.aggregate == MilestoneAggregate.high]
    notifiable = _select_notifiable_instance_ids(records, state, debounce_intervals=10)
    announced = sorted(r.interval for r in highs if r.instance_id in notifiable)

    assert len(highs) == 12, "every extreme in the batch must be persisted"
    # anchor starts at the stored 12:00 record: announce 12:50, then 13:00 is inside that window
    assert announced == [base + timedelta(minutes=50)]
