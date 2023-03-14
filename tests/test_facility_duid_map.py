from opennem.core.facility_duid_map import facility_duid_map


class TestFacilityDuidMap:
    def test_gordon(self):
        subject = "GORDON1"
        value = facility_duid_map(subject)

        assert value == "GORDON", "GORDON1 becomes GORDON as they merged"
