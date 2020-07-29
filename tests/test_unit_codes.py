from opennem.core.unit_codes import duid_is_ocode, get_basecode, get_unit_code
from opennem.core.unit_parser import UnitSchema


class TestUnitCodes(object):
    def test_no_alias(self):
        duid = "TEST1"
        unit = UnitSchema(id=1, number=1)

        unit_code = get_unit_code(unit, duid)

        assert (
            unit_code == "TEST1"
        ), "No alias means unit code is the same as duid"

    def test_with_alias(self):
        duid = "TEST1"
        unit = UnitSchema(id=1, number=1, alias="GT1")

        unit_code = get_unit_code(unit, duid)

        assert unit_code == "TEST1_GT1", "Unit with GT1 alias"

    def test_with_basecode(self):
        duid = None
        unit = UnitSchema(id=1, number=1, alias=None)
        station_name = "Portland"

        unit_code = get_unit_code(unit, duid, station_name)
        assert unit_code == "0NPOR_1", "Unit code is right with no duid"

    def test_basecode(self):
        station_name = "Pioneer Sugar Mill"
        subject = get_basecode(station_name)

        assert subject == "0NPSM", "Pioneer sugar mill becomes 0NPSM"

    def test_basecode_single_word(self):
        station_name = "Portland"
        subject = get_basecode(station_name)

        assert subject == "0NPOR", "Portland becomes 0NPOR"

    def test_basecode_five_words(self):
        station_name = "Portland Portland Portland Portland Portland"
        subject = get_basecode(station_name)

        assert subject == "0NPPPP", "Portland becomes 0NPPPP"

    def test_is_temp_ocode(self):
        ocode = "0NPSM"
        subject = duid_is_ocode(ocode)

        assert subject == True, "0NPSM is an ocode"
