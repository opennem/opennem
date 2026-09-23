"""Tests for in-batch re-anchoring in check_and_persist_milestones_chunked.

The persistence layer keeps EVERY genuine new extreme for BOTH the live incremental path (one
record per record_id per call) and the backlog/reconciliation path (many records per record_id in
one batch, sorted ascending). The batch path relies on the local re-anchoring state because the
global milestone_state is not updated mid-batch.

The interval debounce used to live here and dropped records inside its window, decimating the
stored chain (#651) — it is now a notification-only gate in
`opennem.recordreactor.utils.should_notify_milestone`, so persistence must be indifferent to it.
These tests exercise the batch path with the DB mocked out — the function returns the records it
kept, which is exactly the decision under test.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from opennem import settings
from opennem.recordreactor import persistence as persistence_mod
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestonePeriod,
    MilestoneRecordSchema,
    MilestoneType,
    MilestoneUnitSchema,
)
from opennem.schema.network import NetworkNEM


def _unit(unit_value: str = "MW") -> MilestoneUnitSchema:
    return MilestoneUnitSchema(name="power_mega", label="Megawatts", unit=unit_value, output_format="{value} {unit}")


def _rec(
    value: float,
    interval: datetime,
    instance_id: uuid.UUID,
    period: MilestonePeriod = MilestonePeriod.interval,
    metric: MilestoneType = MilestoneType.power,
    unit_value: str = "MW",
) -> MilestoneRecordSchema:
    return MilestoneRecordSchema(
        interval=interval,
        aggregate=MilestoneAggregate.high,
        metric=metric,
        period=period,
        network=NetworkNEM,
        unit=_unit(unit_value),
        network_region="NSW1",
        fueltech=None,
        value=value,
        instance_id=instance_id,
    )


class _FakeSession:
    async def execute(self, *args, **kwargs):
        return None

    async def commit(self):
        return None

    async def rollback(self):
        return None


class _FakeWriteSessionCtx:
    async def __aenter__(self):
        return _FakeSession()

    async def __aexit__(self, *exc):
        return False


@pytest.fixture
def mock_db(monkeypatch):
    """Mock the milestone state (empty) and the write session (no-op)."""

    async def _empty_state():
        return {}

    monkeypatch.setattr(persistence_mod, "get_current_milestone_state", _empty_state)
    monkeypatch.setattr(persistence_mod, "get_write_session", lambda: _FakeWriteSessionCtx())


@pytest.mark.asyncio
@pytest.mark.parametrize("debounce", [0, 10])
async def test_batch_keeps_every_consecutive_interval_record(monkeypatch, mock_db, debounce: int):
    """A monotonic ramp (one new high every interval) is kept in full, whatever the debounce.

    #651: keeping only the first value in each debounce window threw away the actual peak, so a
    later lower value beat the decimated chain and published as an all-time record.
    """
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", debounce)

    base = datetime(2026, 5, 31, 12, 0)
    iids = [uuid.uuid4() for _ in range(13)]
    # 13 records at 5-min steps (12:00 .. 13:00), each a new high
    records = [_rec(value=100 + i * 20, interval=base + timedelta(minutes=5 * i), instance_id=iids[i]) for i in range(13)]

    kept = await persistence_mod.check_and_persist_milestones_chunked(records)

    assert [r.interval for r in kept] == [base + timedelta(minutes=5 * i) for i in range(13)]
    # the true peak survives
    assert kept[-1].value == max(r.value for r in records)
    # chain links each record to its immediate predecessor
    assert kept[0].previous_instance_id is None
    assert [r.previous_instance_id for r in kept[1:]] == iids[:-1]


@pytest.mark.asyncio
async def test_batch_still_drops_records_that_do_not_beat_the_chain(monkeypatch, mock_db):
    """The value comparison is untouched: a lower value mid-ramp is not a record."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 10)

    base = datetime(2026, 5, 31, 12, 0)
    records = [
        _rec(value=100, interval=base, instance_id=uuid.uuid4()),
        _rec(value=90, interval=base + timedelta(minutes=5), instance_id=uuid.uuid4()),
        _rec(value=150, interval=base + timedelta(minutes=10), instance_id=uuid.uuid4()),
    ]

    kept = await persistence_mod.check_and_persist_milestones_chunked(records)

    assert [r.value for r in kept] == [100, 150]


@pytest.mark.asyncio
async def test_batch_keeps_day_records(monkeypatch, mock_db):
    """Day+ period records are spaced far apart and are never debounced."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 10)

    iids = [uuid.uuid4(), uuid.uuid4()]
    records = [
        _rec(1000, datetime(2026, 5, 29), iids[0], period=MilestonePeriod.day, metric=MilestoneType.energy, unit_value="MWh"),
        _rec(1100, datetime(2026, 5, 30), iids[1], period=MilestonePeriod.day, metric=MilestoneType.energy, unit_value="MWh"),
    ]

    kept = await persistence_mod.check_and_persist_milestones_chunked(records)

    assert len(kept) == 2
    # chain intact across kept day records
    assert kept[1].previous_instance_id == iids[0]
