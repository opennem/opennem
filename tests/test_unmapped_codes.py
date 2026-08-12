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


def test_interconnectors_are_skipped():
    """No fueltech by design; flows are handled by a separate pipeline."""
    rows = [
        ("NEM", "VIC1-NSW1", 80920.0, 2131),
        ("NEM", "N-Q-MNSP1", -2855.0, 2131),
        ("NEM", "V-SA", -23644.0, 2131),
        ("NEM", "T-V-MNSP1", 8921.0, 2131),
    ]

    assert filter_dropped(rows, REASON_NO_FUELTECH) == []


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
