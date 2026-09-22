"""Regression guard for #656: an empty chain must not turn the next observation into a record.

`_map_row_to_records` appended a candidate with no comparison whenever `current_state` held no
record for its record_id, for both aggregates. An hour after the fixes for #651-#654 deployed to
dev, the worker wrote `au.wem.solar.energy.day.low` = 18,527 MWh for 21 Sep — the *highest* of the
surrounding six days (16,744 / 17,639 / 13,103 / 14,012 / 12,563 / 18,527), recorded as an all-time
low, because the cutoff bug in #656 had left that chain empty.

#654 closed the same hole at the backlog's window edge. This is the live incremental path.
"""

import uuid
from datetime import datetime

import pytest

from opennem.recordreactor.incremental import _map_row_to_records
from opennem.recordreactor.metric_registry import (
    GROUPING_FUELTECH,
    GROUPING_NETWORK,
    get_metric_registry,
)
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestonePeriod,
    MilestoneRecordOutputSchema,
    MilestoneType,
)
from opennem.schema.network import NetworkWEM

ENERGY = next(m for m in get_metric_registry() if m.metric == MilestoneType.energy)
POWER = next(m for m in get_metric_registry() if m.metric == MilestoneType.power)

# the day the dev worker recorded as an all-time low, and its value
INCIDENT_DAY = datetime(2026, 9, 21)
INCIDENT_VALUE = 18527.4
# the real low of that week
WEEK_LOW = 12563.3


def _map(value, interval, current_state, unseeded=None, metric_def=ENERGY, period=MilestonePeriod.day):
    return _map_row_to_records(
        row={"time_bucket": interval, "value": value, "interval_count": 288, "fueltech_group_id": "solar"},
        metric_def=metric_def,
        grouping=GROUPING_FUELTECH,
        period=period,
        network=NetworkWEM,
        current_state=current_state,
        unseeded_record_ids=unseeded,
    )


def _chain(record_id: str, value: float, interval: datetime) -> MilestoneRecordOutputSchema:
    return MilestoneRecordOutputSchema(
        record_id=record_id,
        interval=interval,
        instance_id=uuid.uuid4(),
        aggregate=record_id.rsplit(".", 1)[-1],
        metric="energy",
        period="day",
        significance=5,
        value=value,
        value_unit="MWh",
        network_id="WEM",
    )


def test_the_incident_row_is_not_a_record_against_an_empty_chain() -> None:
    """au.wem.solar.energy.day.low, 21 Sep 2026: the week's maximum, written as its minimum."""
    unseeded: set[str] = set()

    records = _map(INCIDENT_VALUE, INCIDENT_DAY, {}, unseeded)

    assert records == []
    assert "au.wem.solar.energy.day.low" in unseeded
    assert "au.wem.solar.energy.day.high" in unseeded


def test_both_aggregates_are_skipped_on_an_empty_chain() -> None:
    """A single observation says nothing about either extreme."""
    unseeded: set[str] = set()

    assert _map(INCIDENT_VALUE, INCIDENT_DAY, {}, unseeded) == []
    assert unseeded == {"au.wem.solar.energy.day.high", "au.wem.solar.energy.day.low"}


def test_a_seeded_chain_still_records_a_genuine_low() -> None:
    """The guard is about the empty chain, not about lows — an established chain works as before."""
    state = {
        "au.wem.solar.energy.day.low": _chain("au.wem.solar.energy.day.low", 13000.0, datetime(2026, 9, 18)),
        "au.wem.solar.energy.day.high": _chain("au.wem.solar.energy.day.high", 30000.0, datetime(2026, 9, 18)),
    }

    records = _map(WEEK_LOW, datetime(2026, 9, 20), state)

    assert [r.aggregate for r in records] == [MilestoneAggregate.low]
    assert records[0].value == round(WEEK_LOW)  # energy records round to whole MWh


def test_a_seeded_chain_rejects_the_incident_value() -> None:
    """With a chain in place the 18,527 MWh day is neither a high nor a low."""
    state = {
        "au.wem.solar.energy.day.low": _chain("au.wem.solar.energy.day.low", 12563.3, datetime(2026, 9, 20)),
        "au.wem.solar.energy.day.high": _chain("au.wem.solar.energy.day.high", 30000.0, datetime(2026, 9, 20)),
    }

    assert _map(INCIDENT_VALUE, INCIDENT_DAY, state) == []


def test_half_seeded_chain_only_records_the_seeded_aggregate() -> None:
    """A chain per aggregate: the high can be established while the low is not."""
    state = {
        "au.wem.solar.energy.day.high": _chain("au.wem.solar.energy.day.high", 15000.0, datetime(2026, 9, 18)),
    }
    unseeded: set[str] = set()

    records = _map(INCIDENT_VALUE, INCIDENT_DAY, state, unseeded)

    assert [r.aggregate for r in records] == [MilestoneAggregate.high]
    assert unseeded == {"au.wem.solar.energy.day.low"}


def test_collector_is_optional() -> None:
    """The caller may not want the report; the guard still holds."""
    assert _map(INCIDENT_VALUE, INCIDENT_DAY, {}) == []


@pytest.mark.parametrize("period", [MilestonePeriod.interval, MilestonePeriod.day, MilestonePeriod.month])
def test_guard_applies_at_every_period(period: MilestonePeriod) -> None:
    metric_def = POWER if period == MilestonePeriod.interval else ENERGY

    assert _map(INCIDENT_VALUE, INCIDENT_DAY, {}, metric_def=metric_def, period=period) == []


def test_network_total_series_is_guarded_too() -> None:
    """Not fueltech-specific — any record_id with no chain is skipped."""
    records = _map_row_to_records(
        row={"time_bucket": INCIDENT_DAY, "value": 50000.0, "interval_count": 288},
        metric_def=ENERGY,
        grouping=GROUPING_NETWORK,
        period=MilestonePeriod.day,
        network=NetworkWEM,
        current_state={},
    )

    assert records == []
