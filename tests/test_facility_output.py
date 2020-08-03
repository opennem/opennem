from random import choice

import pytest

from opennem.db.load_fixtures import load_fixture as load_db_fixture
from opennem.utils.tests import load_fixture


class TestStationOutput(object):
    """
        Tests of the station output for essential sanity checks.

    """

    data = {}
    statuses = None

    @classmethod
    def setup_class(cls):
        """
            Load the stations fixture for this test suite
        """
        cls.data = load_fixture("stations.json")
        cls.statuses = load_db_fixture("fueltechs.json")
        cls.fueltechs = load_db_fixture("facility_status.json")

    def get_random_station(self):
        return choice(self.data)

    def test_schema_entry(self):
        """
            There should be at least one entry
        """
        data_length = len(self.data)
        assert data_length > 0, "Station data is valid and has a length"

    def test_schema_datatypes(self):
        """
            The fields should be of correct data type
        """

        data_types = {
            "name": str,
            "ocode": str,
            "code": str,
            "region": str,
            "status": str,
            "fueltech": str,
            "unit_id": int,
            "unit_num": int,
            "unit_cap": float,
            "station_cap_agg": float,
            "station_cap_registered": float,
            "added_by": str,
            "updated_by": str,
        }

        subject = self.get_random_station()

        for subject_field, subject_value in subject.items():
            assert type(subject_value) in [
                data_types[subject_field],
                None,
            ], "{} is of type {}".format(
                subject_value, data_types[subject_field]
            )

    def test_nem_single(self):
        """
            There should be at least one NSW station
        """
        nsw_data = list(filter(lambda x: x["region"] == "NSW1", self.data))
        assert len(nsw_data) > 0, "There is at least one NSW station"

    def test_wem_single(self):
        """
            There should be at least one WA facility
        """
        wem_data = list(filter(lambda x: x["region"] == "WEM", self.data))
        assert len(wem_data) > 0, "There is at least one WEM station"

    def test_valid_status_types(self):

        status_list = [i["status"] for i in self.data]
        status_set = list(set(status_list))

    def test_returns_string_one(self):
        pass

    def test_broken_hill(self):
        """
            Broken Hill has two stations
        """
        pass

    def test_hume(self):
        """
            Hume has two stations - one in VIC and one in NSW
        """
        pass

    def test_hornsdale(self):
        """
            HPRG1 is discharging, HPRL1 is charging
        """
        pass

    def test_hallett(self):
        """ Hallett has a gas station and a wind farm

            gas - AGLHAL
            wind - HALLWF1
        """
        pass

    def test_sa_vpp(self):
        """
            SA VPP has name SA VPP and is aggregate vpp
        """
        pass

    def test_dalrymple(self):
        """
            Dalrymple DALNTH has one charging one discharging battery unit
        """
        pass

    def test_bolivar(self):
        """
            Bolivar (BOLIVAR) is biogas
        """
        pass

    def test_angaston(self):
        """
            Angaston (ANGASTON) has 1 unit of capacity 50
        """
        pass

    def test_victoria_mill(self):
        """
            Victoria Mill (VICMILL) has two units 24MW capacity
        """
        pass
