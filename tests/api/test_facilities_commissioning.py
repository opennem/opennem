"""Tests for the derived commissioning unit status (GH openelectricity-typescript#21).

A unit is served as `commissioning` when it is operating but its maximum observed
generation is <= 90% of capacity. The status is derived at the API layer and never
stored — mirrors the OpenElectricity website rule.
"""

from types import SimpleNamespace

from opennem.api.facilities.router import _unit_effective_status
from opennem.schema.unit import UnitStatusType


def _unit(
    status_id: str = "operating",
    max_generation: float | None = None,
    capacity_maximum: float | None = None,
    capacity_registered: float | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        status_id=status_id,
        max_generation=max_generation,
        capacity_maximum=capacity_maximum,
        capacity_registered=capacity_registered,
    )


def test_operating_at_full_output_stays_operating() -> None:
    assert _unit_effective_status(_unit(max_generation=95.0, capacity_registered=100.0)) == "operating"


def test_operating_below_threshold_is_commissioning() -> None:
    assert _unit_effective_status(_unit(max_generation=50.0, capacity_registered=100.0)) == "commissioning"


def test_exactly_at_threshold_is_commissioning() -> None:
    assert _unit_effective_status(_unit(max_generation=90.0, capacity_registered=100.0)) == "commissioning"


def test_just_above_threshold_is_operating() -> None:
    assert _unit_effective_status(_unit(max_generation=90.1, capacity_registered=100.0)) == "operating"


def test_capacity_maximum_preferred_over_registered() -> None:
    # 85/110 = 77% of capacity_maximum -> commissioning even though 85/90 > 90% of registered
    assert _unit_effective_status(_unit(max_generation=85.0, capacity_maximum=110.0, capacity_registered=90.0)) == "commissioning"


def test_no_observed_generation_stays_operating() -> None:
    # no data is not evidence of commissioning
    assert _unit_effective_status(_unit(max_generation=None, capacity_registered=100.0)) == "operating"


def test_no_capacity_stays_operating() -> None:
    assert _unit_effective_status(_unit(max_generation=50.0)) == "operating"


def test_committed_not_derived() -> None:
    assert _unit_effective_status(_unit(status_id="committed", max_generation=10.0, capacity_registered=100.0)) == "committed"


def test_retired_not_derived() -> None:
    assert _unit_effective_status(_unit(status_id="retired", max_generation=10.0, capacity_registered=100.0)) == "retired"


def test_commissioning_enum_member_exists() -> None:
    assert UnitStatusType("commissioning") is UnitStatusType.commissioning
