from opennem.core.facility_code import parse_wem_facility_code


class TestWemFacilityCode:
    def test_pinjar(self):
        code = "PINJAR_GT7"
        facility_code = parse_wem_facility_code(code)

        assert facility_code == "PINJAR", "Facility code is Pinjar"

    def test_west_kalgoorlie(self):
        code = "WEST_KALGOORLIE_GT2"
        facility_code = parse_wem_facility_code(code)

        assert facility_code == "WEST_KALGOORLIE", "Facility code is WEST_KALGOORLIE"

    def test_bridgerown(self):
        code = "BRIDGETOWN_BIOMASS_PLANT"
        facility_code = parse_wem_facility_code(code)

        assert facility_code == "BRIDGETOWN_BIOMASS_PLANT", "Bridgetown remains the same"

    def test_gosnells(self):
        code = "GOSNELLS"
        facility_code = parse_wem_facility_code(code)

        assert facility_code == "GOSNELLS", "Gosnells stations is the same"
