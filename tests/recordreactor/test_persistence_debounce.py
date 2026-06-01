"""Tests for interval-record debounce + in-batch re-anchoring in
check_and_persist_milestones_chunked.

The persistence layer is the authoritative debounce gate for BOTH the live
incremental path (one record per record_id per call) and the backlog/
reconciliation path (many records per record_id in one batch, sorted ascending).
The backlog case relies on the local re-anchoring state because the global
milestone_state is not updated mid-batch. These tests exercise that batch path
with the DB mocked out — the function returns the records it kept, which is
exactly the debounce decision.
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
async def test_batch_debounces_consecutive_interval_records(monkeypatch, mock_db):
    """A monotonic ramp (one new high every interval) is kept once per window."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 10)

    base = datetime(2026, 5, 31, 12, 0)
    iids = [uuid.uuid4() for _ in range(13)]
    # 13 records at 5-min steps (12:00 .. 13:00), each a new high
    records = [_rec(value=100 + i * 20, interval=base + timedelta(minutes=5 * i), instance_id=iids[i]) for i in range(13)]

    kept = await persistence_mod.check_and_persist_milestones_chunked(records)

    # window = 10 intervals = 50m -> keep 12:00, then next at 12:50, rest suppressed
    assert [r.interval for r in kept] == [base, base + timedelta(minutes=50)]
    # first kept has no previous; second kept re-links to the first kept (not a dropped record)
    assert kept[0].previous_instance_id is None
    assert kept[1].previous_instance_id == iids[0]


@pytest.mark.asyncio
async def test_batch_no_debounce_keeps_all_interval_records(monkeypatch, mock_db):
    """Setting 0 disables debouncing — every new high is kept."""
    monkeypatch.setattr(settings, "milestone_interval_debounce_intervals", 0)

    base = datetime(2026, 5, 31, 12, 0)
    records = [_rec(value=100 + i * 20, interval=base + timedelta(minutes=5 * i), instance_id=uuid.uuid4()) for i in range(5)]

    kept = await persistence_mod.check_and_persist_milestones_chunked(records)

    assert len(kept) == 5


@pytest.mark.asyncio
async def test_batch_does_not_debounce_day_records(monkeypatch, mock_db):
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
