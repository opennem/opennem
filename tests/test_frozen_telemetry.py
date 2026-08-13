"""Frozen telemetry detection (#544).

The detector's whole value is that it separates a genuine fault from the flat runs that
normal solar operation produces all the time, so the tests are mostly about what it
declines to flag.
"""

from opennem.monitors.frozen_telemetry import (
    CAPACITY_FRACTION,
    MIN_NIGHT_INTERVALS,
    NIGHT_END_HOUR,
    NIGHT_START_HOUR,
    FrozenSignal,
    to_findings,
)

# (facility_code, network_region, day, capacity, intervals, min_mw, max_mw)
BUSF1_ROW = ("BUSF1", "QLD1", "2026-04-30", 101.0, 60, 60.76, 60.76)


def test_busf1_is_flagged_as_a_freeze():
    """The incident that prompted the check has to come out as a frozen signal."""
    (finding,) = to_findings([BUSF1_ROW])

    assert finding.facility_code == "BUSF1"
    assert finding.is_constant
    assert "flat at 60.76 MW" in str(finding)


def test_varying_night_output_is_reported_but_not_called_a_freeze():
    """Middlemount swung 6-24 MW overnight — wrong, but a different fault to a stuck signal."""
    (finding,) = to_findings([("MIDDLSF1", "QLD1", "2026-03-17", 30.0, 7, 6.8, 23.8)])

    assert not finding.is_constant
    assert "6.80-23.80 MW" in str(finding)


def test_findings_are_ordered_worst_first():
    rows = [
        ("GOONSF1", "NSW1", "2026-07-23", 85.0, 10, 23.77, 23.77),
        BUSF1_ROW,
        ("NEVERSF1", "NSW1", "2026-02-25", 132.0, 16, 32.94, 32.94),
    ]

    assert [f.intervals for f in to_findings(rows)] == [60, 16, 10]


def test_night_window_is_dark_across_the_whole_nem():
    """Latest civil twilight anywhere in the NEM ends before 21:30 AEST."""
    assert NIGHT_START_HOUR >= 22
    assert NIGHT_END_HOUR <= 3


def test_thresholds_clear_overnight_auxiliary_load():
    """Solar farms idle around 0.01-0.2 MW overnight. On the smallest NEM solar unit
    (~12 MW) the capacity floor still sits well above that."""
    smallest_solar_capacity_mw = 12.0

    assert CAPACITY_FRACTION * smallest_solar_capacity_mw > 0.2


def test_minimum_run_is_at_least_half_an_hour():
    """One interval either side of dusk is a timestamp edge, not a fault."""
    assert MIN_NIGHT_INTERVALS * 5 >= 30


def test_constant_tolerance_is_tight_enough_to_split_real_cases():
    """BUSF1 froze to the cent; the near-miss cases moved by more than that."""
    frozen = FrozenSignal("BUSF1", "QLD1", "2026-04-30", 101.0, 60, 60.76, 60.76)
    drifting = FrozenSignal("BUSF1", "QLD1", "2026-04-09", 101.0, 13, 73.65, 73.71)

    assert frozen.is_constant
    assert not drifting.is_constant
