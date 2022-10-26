
from opennem.core.unit_parser import unit_has_alias


class TestUnitHasAlias(object):
    def test_single_number(self):
        assert unit_has_alias("1") is False, "Unit single number has no alias"

    def test_range_number(self):
        assert unit_has_alias("1-2") is False, "Unit number range has no alias"

    def test_range_with_spaces_number(self):
        assert (
            unit_has_alias("1 - 50") is False
        ), "Unit space with range has no alias"

    def test_unit_alias_single(self):
        assert unit_has_alias("GT1") is True, "Unit single no space has alias"

    def test_unit_space_alias_single(self):
        assert (
            unit_has_alias("GT 1") is True
        ), "Unit single with space has alias"

    def test_unit_space_with_range(self):
        assert (
            unit_has_alias("WSB 1-50") is True
        ), "Unit space with range has alias"

    def test_unit_alias_single_appended(self):
        assert unit_has_alias("1a") is True, "Unit single appended alias"
