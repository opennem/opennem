"""Synthetic "0" prefix must not swallow a real facility (#481).

The prefix marks a code OpenNEM invented, and stripping it recovers the operational code.
That only holds while the stripped result is unclaimed: `0WNSF` (Winton North) strips to
`WNSF`, which is a real and entirely different facility (Wangaratta). The old rule dropped
whichever one it saw second, so Winton North never reached Postgres — its CMS location and
osm_way_id were correct and unreachable.
"""

import pytest

from opennem.cms.queries import DuplicateCodeError, _validate_unique_codes
from opennem.cms.utils import resolve_operational_code, strip_synthetic_prefix
from opennem.schema.facility import FacilitySchema


def _facility(code: str, cms_id: str, unit_codes: list[str] | None = None) -> FacilitySchema:
    return FacilitySchema(
        code=code,
        name=code.title(),
        network_id="NEM",
        network_region="NSW1",
        _id=cms_id,
        units=[
            {
                "code": unit_code,
                "dispatch_type": "GENERATOR",
                "fueltech_id": "solar_utility",
                "status_id": "operating",
            }
            for unit_code in (unit_codes or [f"{code}1"])
        ],
    )


class TestResolveOperationalCode:
    def test_strips_an_unclaimed_synthetic_prefix(self):
        assert resolve_operational_code("0QBYNBG1", reserved=set()) == ("QBYNBG1", "0QBYNBG1")

    def test_keeps_the_prefix_when_the_stripped_code_is_claimed(self):
        assert resolve_operational_code("0WNSF", reserved={"WNSF"}) == ("0WNSF", "0WNSF")

    def test_leaves_a_non_synthetic_code_alone(self):
        assert resolve_operational_code("WNSF", reserved={"0WNSF"}) == ("WNSF", "WNSF")

    def test_a_leading_zero_before_a_digit_is_not_a_prefix(self):
        """Only 0-then-letter is the synthetic marker, matching strip_synthetic_prefix."""
        assert resolve_operational_code("01ABC", reserved=set()) == strip_synthetic_prefix("01ABC")


class TestValidateUniqueCodes:
    def test_both_facilities_survive_a_prefix_collision(self):
        facilities = _validate_unique_codes([_facility("0WNSF", "cms-winton"), _facility("WNSF", "cms-wangaratta")])

        assert len(facilities) == 2
        by_code = {f.code: f for f in facilities}
        assert by_code["0WNSF"].operational_code == "0WNSF"
        assert by_code["WNSF"].operational_code == "WNSF"

    @pytest.mark.parametrize("order", [("0WNSF", "WNSF"), ("WNSF", "0WNSF")])
    def test_resolution_does_not_depend_on_payload_order(self, order):
        """The old rule kept whichever came first, so the real facility could be the one dropped."""
        facilities = _validate_unique_codes([_facility(code, f"cms-{code}") for code in order])

        assert {f.operational_code for f in facilities} == {"0WNSF", "WNSF"}
        assert len(facilities) == 2

    def test_synthetic_prefix_is_still_stripped_when_uncontested(self):
        """The QBYNB battery split is the normal case and must keep working."""
        facilities = _validate_unique_codes([_facility("QBYNB", "cms-q", ["QBYNB1", "0QBYNBG1", "0QBYNBL1"])])

        units = {u.code: u for u in facilities[0].units}
        assert units["0QBYNBG1"].operational_code == "QBYNBG1"
        assert units["0QBYNBG1"].display_code == "0QBYNBG1"
        assert units["QBYNB1"].operational_code == "QBYNB1"

    def test_colliding_unit_codes_across_facilities_both_survive(self):
        facilities = _validate_unique_codes([_facility("WINTONN", "cms-a", ["0WNSF1"]), _facility("WANGA", "cms-b", ["WNSF1"])])

        resolved = {u.code: u.operational_code for f in facilities for u in f.units}
        assert resolved == {"0WNSF1": "0WNSF1", "WNSF1": "WNSF1"}

    def test_a_true_duplicate_still_raises(self):
        with pytest.raises(DuplicateCodeError):
            _validate_unique_codes([_facility("WNSF", "cms-a"), _facility("WNSF", "cms-b")])

    def test_nothing_is_dropped_for_a_prefix_collision(self):
        """Regression guard: the failure mode was silent, so assert on the count directly."""
        payload = [_facility("0WNSF", "cms-1"), _facility("WNSF", "cms-2"), _facility("QBYNB", "cms-3")]

        assert len(_validate_unique_codes(payload)) == 3
