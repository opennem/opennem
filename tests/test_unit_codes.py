from opennem.core.unit_codes import get_basecode, get_unit_code
from opennem.core.unit_parser import UnitSchema


class TestUnitCodes(object):
    def test_no_alias(self):
        duid = "TEST1"
        unit = UnitSchema(id=1, number=1)

        unit_code = get_unit_code(duid, unit)

        assert (
            unit_code == "TEST1"
        ), "No alias means unit code is the same as duid"

    def test_with_alias(self):
        duid = "TEST1"
        unit = UnitSchema(id=1, number=1, alias="GT1")

        unit_code = get_unit_code(duid, unit)

        assert unit_code == "TEST1_GT1", "Unit with GT1 alias"

    def test_basecode(self):
        station_name = "Pioneer Sugar Mill"
        subject = get_basecode(station_name)

        assert subject == "0NPSM", "Pioneer sugar mill becomes 0NPSM"
