from opennem.core.unit_codes import duid_is_ocode, get_basecode, get_unit_code
from opennem.core.unit_parser import UnitSchema


class TestUnitCodes:
    def test_no_alias(self):
        duid = "TEST1"
        unit = UnitSchema(id=1, number=1)

        unit_code = get_unit_code(unit, duid)

        assert unit_code == "TEST1", "No alias means unit code is the same as duid"

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
        assert unit_code == "0NPORT_1", "Unit code is right with no duid"

    def test_basecode(self):
        station_name = "Pioneer Sugar Mill"
        subject = get_basecode(station_name)

        assert subject == "0NPISUMI", "Pioneer sugar mill becomes 0NPISUMI"

    def test_basecode_single_word(self):
        station_name = "Portland"
        subject = get_basecode(station_name)

        assert subject == "0NPORT", "Portland becomes 0NPOR"

    def test_basecode_five_words(self):
        station_name = "Portland Portland Portland Portland Portland"
        subject = get_basecode(station_name)

        assert subject == "0NPPPPP", "Portland becomes 0NPPPP"

    def test_is_temp_ocode(self):
        ocode = "0NPSM"
        subject = duid_is_ocode(ocode)

        assert subject is True, "0NPSM is an ocode"

    def test_basecode_brackets(self):
        subject = get_basecode("Snowy River Scheme (Unit)")

        assert subject == "0NSRSU", "Parses out junk characters correctly"

    def test_basecode_periods(self):
        subject = get_basecode("Snowy River Scheme 2.0")

        assert subject == "0NSRS20", "Parses out junk characters correctly"

    def test_short(self):
        subject = get_basecode("Todae DHP")

        assert subject == "0NTODDHP", "Attaches acronyms correctly "

    def test_uniqueness(self):
        subject_1 = get_basecode("Todae La Trobe University Bendigo")
        subject_2 = get_basecode("Todae Solar - Nillumbik")

        assert subject_1 != subject_2, "These two should be unique basecodes"
