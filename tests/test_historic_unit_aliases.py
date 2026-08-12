"""Historic single-direction DUID aliasing (#603).

The retired bouldercombe/dalrymple duids carry a single direction each and must be
aliased 1:1 onto the paired gen/load codes — never sign-split, which would route the
generation code's small negative auxiliary draw into the charge unit and double count
against the real charge duid.
"""

from opennem.core.battery import HISTORIC_UNIT_ALIASES, _generate_manual_battery_unit_map


def test_historic_duids_map_to_the_paired_codes():
    assert HISTORIC_UNIT_ALIASES == {
        "BBATTERY": "BBATTERYG1",
        "BBATRYL1": "BBATTERYL1",
        "DALNTH01": "DALNTHG1",
    }


def test_aliased_duids_are_not_also_sign_split():
    """The two maps must stay disjoint.

    `is_battery_unit()` matches on duid, so a code in both maps would be sign-split *and*
    aliased, producing double-counted charge rows. "BBATTERY" was in the battery map as a
    station code and collided with the duid of the same name.
    """
    battery_map = _generate_manual_battery_unit_map()

    overlap = set(HISTORIC_UNIT_ALIASES) & set(battery_map)

    assert not overlap, f"codes are both aliased and sign-split: {sorted(overlap)}"


def test_bidirectional_units_are_still_sign_split():
    """The real bidirectional duids must keep their split — only the historic ones moved."""
    battery_map = _generate_manual_battery_unit_map()

    assert battery_map["BBATTERY1"].charge_unit == "BBATTERYL1"
    assert battery_map["BBATTERY1"].discharge_unit == "BBATTERYG1"
    assert battery_map["DALNTH1"].charge_unit == "DALNTHL1"
    assert battery_map["DALNTH1"].discharge_unit == "DALNTHG1"


def test_alias_targets_are_never_themselves_aliased():
    """No chaining — an alias target must be a terminal code."""
    assert not set(HISTORIC_UNIT_ALIASES.values()) & set(HISTORIC_UNIT_ALIASES)
