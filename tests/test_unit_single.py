
from opennem.core.unit_single import facility_unit_numbers_are_single


class TestUnitSingle(object):
    def test_is_a_single_unit(self):
        subj = facility_unit_numbers_are_single("TEST")
        assert (
            subj == False
        ), "TEST is not a facility with single unit unit numbers"

    def test_returns_int_one(self):
        subj = facility_unit_numbers_are_single("AGLHAL")
        assert (
            subj == True
        ), "AGLHAL is a facility with single unit unit numbers"
