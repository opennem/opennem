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

    # disabled
    def _test_schema_datatypes(self):
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
            "lat": float,
            "lng": float,
            "added_by": str,
            "updated_by": str,
        }

        subject = self.get_random_station()

        for subject_field, subject_value in subject.items():
            if subject_value:
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

    # disabled
    def _test_wem_single(self):
        """
            There should be at least one WA facility
        """
        wem_data = list(filter(lambda x: x["region"] == "WEM", self.data))
        assert len(wem_data) > 0, "There is at least one WEM station"

    def test_valid_status_types(self):

        status_list = [i["status"] for i in self.data]
        status_set = list(set(status_list))

        assert "operating" in status_set, "Have operating units"
        assert "retired" in status_set, "Have retired units"

    def test_broken_hill(self):
        """
            Broken Hill has two stations
        """
        broken_hills = list(
            filter(lambda x: x["name"] == "Broken Hill", self.data)
        )
        broken_hills_stations = list(set([x["ocode"] for x in broken_hills]))

        assert len(broken_hills_stations) == 2, "Have two broken hill stations"

    def test_hume(self):
        """
            Hume has two stations - one in VIC and one in NSW
        """
        hume_stations = list(filter(lambda x: x["name"] == "Hume", self.data))
        hume_states = [x["region"] for x in hume_stations]

        assert len(hume_stations) == 2, "There are two Hume Stations"
        assert "NSW1" in hume_states, "There is a hume station in NSW"
        assert "VIC1" in hume_states, "There is a hume station in VIC"

    def test_hornsdale(self):
        """
            HPRG1 is discharging, HPRL1 is charging
        """
        hprg1 = list(filter(lambda x: x["code"] == "HPRG1", self.data))[0]
        hprl1 = list(filter(lambda x: x["code"] == "HPRL1", self.data))[0]

        assert (
            hprg1["fueltech"] == "battery_discharging"
        ), "HPRG1 is discharging"
        assert hprl1["fueltech"] == "battery_charging", "HPRL1 is charging"

    def test_hallett(self):
        """ Hallett has a gas station and a wind farm

            gas - AGLHAL
            wind - HALLWF1
        """
        aglhal = list(filter(lambda x: x["code"] == "AGLHAL", self.data))[0]
        hallwf = list(filter(lambda x: x["code"] == "HALLWF1", self.data))[0]

        assert aglhal["fueltech"] == "gas_ocgt", "AGLHAL is gas"
        assert hallwf["fueltech"] == "wind", "HALLWF1 is wind"

    # disabled
    def _test_sa_vpp(self):
        """
            SA VPP has name SA VPP and is aggregate vpp
        """
        savpp = list(filter(lambda x: x["name"] == "SA VPP", self.data))

        assert type(savpp) is list, "We have an SA VPP entry"
        assert len(savpp) == 1, "We have one SA VPP entry"

        savpp_rec = savpp.pop()
        assert (
            savpp_rec["fueltech"] == "battery_discharging"
        ), "The SA VPP fueltech is aggregate vpp"

    def test_midlands(self):
        """
            There should be one midlands station
        """
        midlands_facilities = list(
            filter(lambda x: x["name"] == "Midlands", self.data)
        )
        midlands = list(set([i["ocode"] for i in midlands_facilities]))

        assert len(midlands) == 1, "There should be one midlands entry"

    def test_pioneer(self):
        """
            There should be one Pioneer Sugar Mill
        """
        pioneer_facilities = list(
            filter(lambda x: x["name"] == "Pioneer Sugar Mill", self.data)
        )
        pioneer = list(set([i["ocode"] for i in pioneer_facilities]))

        assert (
            len(pioneer) == 1
        ), "There should be one Pioneer Sugar Mill entry"

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

    # Station duid mapping tests
    """

        hallet, snowtown and hornsdale all have station => duid remaps
    """

    def test_snowtown_map(self):
        pass
