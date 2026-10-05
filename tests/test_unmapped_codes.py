"""Filtering logic for the dropped-facility-code monitor (#604)."""

from opennem.monitors.unmapped_codes import (
    REASON_NO_FUELTECH,
    REASON_NO_UNIT,
    DroppedCode,
    filter_dropped,
)


def test_unmapped_code_with_energy_is_reported():
    rows = [("WEM", "NEWCODE1", 1234.5, 288)]

    findings = filter_dropped(rows, REASON_NO_UNIT)

    assert findings == [DroppedCode(network_id="WEM", code="NEWCODE1", reason=REASON_NO_UNIT, energy_mwh=1234.5, intervals=288)]


def test_known_unmapped_codes_are_skipped():
    """bouldercombe/dalrymple are deliberately unmapped — see #603."""
    rows = [("NEM", "BBATTERY", 900.0, 288), ("NEM", "DALNTH01", 400.0, 288)]

    assert filter_dropped(rows, REASON_NO_UNIT) == []


def test_unmapped_interconnector_is_reported():
    """The flows aggregate inner joins units too, so a new interconnector is dropped until mapped (#650).

    A code pattern skip (`-SA1`) hid PEC's NSW1-SA1. Mapped interconnectors are excluded in the
    unjoinable query by `units.interconnector`, never by their code.
    """
    rows = [("NEM", "NSW1-SA1", -1938.3, 1539)]

    findings = filter_dropped(rows, REASON_NO_UNIT)

    assert [f.code for f in findings] == ["NSW1-SA1"]


def test_negative_energy_still_reported():
    """A dropped load is as much a hole in the data as a dropped generator."""
    rows = [("WEM", "SOMELOAD1", -5000.0, 288)]

    findings = filter_dropped(rows, REASON_NO_UNIT)

    assert len(findings) == 1
    assert findings[0].energy_mwh == -5000.0


def test_reason_is_carried_through():
    rows = [("NEM", "ORPHAN1", 10.0, 12)]

    assert filter_dropped(rows, REASON_NO_FUELTECH)[0].reason == REASON_NO_FUELTECH


def test_str_is_readable_for_slack():
    entry = DroppedCode(network_id="WEM", code="NEWCODE1", reason=REASON_NO_UNIT, energy_mwh=19900.456, intervals=12345)

    assert str(entry) == "WEM NEWCODE1 (no units row): 19,900.5 MWh over 12,345 intervals"
