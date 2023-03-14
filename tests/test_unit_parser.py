from opennem.core.unit_parser import parse_unit_duid, parse_unit_number


class TestUnitParser:
    # Simple

    def test_returns_string_one(self):
        subj = parse_unit_number("1")
        assert subj.id == 1, "Returns string 1 as unit number 1"
        assert subj.number == 1, "Unit has one unit"

    def test_returns_string_two(self):
        subj = parse_unit_number("2")
        assert subj.id == 2, "Has unit id of 2"
        assert subj.number == 1, "Unit has one unit"

    def test_returns_int_one(self):
        subj = parse_unit_number(1)
        assert subj.id == 1, "Returns int 1 as unit number 1"
        assert subj.number == 1, "Unit has one unit"

    def test_returns_string_one_padded(self):
        subj = parse_unit_number("  1  ")
        assert subj.id == 1, "Returns string 1 as unit number 1"
        assert subj.number == 1, "Unit has one unit"

    def test_blank_unit_number(self):
        subj = parse_unit_number("")
        assert subj.id == 1, "Returns string 1 as unit number 1"
        assert subj.number == 1, "Unit has one unit"

    def test_none_unit_number(self):
        subj = parse_unit_number(None)
        assert subj.id == 1, "Returns string 1 as unit number 1"
        assert subj.number == 1, "Unit has one unit"

    # Ranges

    def test_simple_range(self):
        subj = parse_unit_number("1-2")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has two units"

    def test_simple_range_padded(self):
        subj = parse_unit_number("1- 2  ")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has two units"

    def test_range_unit_number(self):
        subj = parse_unit_number("1-50")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 50, "Unit has 50 units"

    def test_range_unit_number_shifted(self):
        subj = parse_unit_number("50-99")
        assert subj.id == 50, "Unit has an id of 50"
        assert subj.number == 50, "Unit has 50 units"
        assert subj.alias is None, "Unit has no alias"

    # Aliases
    def test_single_has_alias(self):
        subj = parse_unit_number("1a")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 1, "Unit has 1 unit"
        assert subj.alias == "A", "Unit has alias of A"

    def test_single_has_alias_prepend(self):
        subj = parse_unit_number("WT1")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 1, "Unit has 1 unit"
        assert subj.alias == "WT", "Unit has alias of WT"

    def test_single_long_alias(self):
        subj = parse_unit_number("WKIEWA1")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 1, "Unit has 1 unit"
        assert subj.alias == "WKIEWA", "Unit has alias of WKIEWA"

    def test_single_has_alias_prepend_space(self):
        subj = parse_unit_number("WT 1")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 1, "Unit has 1 unit"
        assert subj.alias == "WT", "Unit has alias of WT"

    def test_range_has_alias(self):
        subj = parse_unit_number("1-2a")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has 2 unit"
        assert subj.alias == "A", "Unit has alias of A"

    def test_range_has_alias_prepend(self):
        subj = parse_unit_number("WT1-2")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has 2 unit"
        assert subj.alias == "WT", "Unit has alias of WT"

    def test_range_has_alias_prepend_space(self):
        subj = parse_unit_number("WT 1-2")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has 2 unit"
        assert subj.alias == "WT", "Unit has alias of WT"

    # Force single

    def test_force_single(self):
        subj = parse_unit_number("GT 1-2", force_single=True)
        assert subj.id == 2, "Unit has an id of 2"
        assert subj.number == 1, "Unit has 1 unit"
        assert subj.alias == "GT1", "Unit has alias of GT1"

    # Multi units in one line

    def test_ampersand(self):
        subj = parse_unit_number("1 & 2")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has 2 units"
        assert subj.alias is None, "Unit has no alias"

    def test_ampersand_three(self):
        subj = parse_unit_number("1 & 2 & 3")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 3, "Unit has 3 units"
        assert subj.alias is None, "Unit has no alias"

    def test_comma_separated(self):
        subj = parse_unit_number("1,2")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has 2 units"
        assert subj.alias is None, "Unit has no alias"

    def test_comma_separated_single(self):
        subj = parse_unit_number("GT 1-2,GT 1-4", force_single=True)
        assert subj.id == 2, "Unit has an id of 1"
        assert subj.number == 2, "Unit has 2 units"
        assert subj.alias == "GT1", "Unit has GT1 alias"

    def test_comma_and_ampersand_separated(self):
        subj = parse_unit_number("1, 2 & 5,3 & 4")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 5, "Unit has 5 units"
        assert subj.alias is None, "Unit has no alias"


class TestUnitDuidParser:
    def test_unit_duid(self):
        subj = parse_unit_duid("WT1-2", "NONE")
        assert subj.id == 1, "Unit has an id of 1"
        assert subj.number == 2, "Unit has 2 unit"
        assert subj.alias == "WT", "Unit has alias of WT"

    def test_unit_duid_single(self):
        subj = parse_unit_duid("GT 1-2", "AGLHAL")
        assert subj.id == 2, "Unit has an id of 2"
        assert subj.number == 1, "Unit has 1 unit"
        assert subj.alias == "GT1", "Unit has alias of GT1"
