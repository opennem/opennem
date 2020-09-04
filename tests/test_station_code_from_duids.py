import pytest

from opennem.core.stations.station_code_from_duids import (
    station_code_from_duids,
)


class TestStationCodeFromDuids(object):
    def test_none(self):
        subject = station_code_from_duids(None)

        assert subject == None, "None is none"

    def test_not_list(self):
        subject = station_code_from_duids("")

        assert subject == None, "None is none"

    def test_empty(self):
        subject = station_code_from_duids([])

        assert subject == None, "None is none"

    def test_barron(self):
        subject = station_code_from_duids(["BARRON1", "BARRON2"])

        assert subject == "BARRON", "Barron convertts to BARRON"

    def test_osbag(self):
        subject = station_code_from_duids(["OSBAG"])

        assert subject == "OSBAG", "OSBAG convertts to OSBAG"

    def test_osbag_two(self):
        subject = station_code_from_duids(["OSBAG", "OSBAG"])

        assert subject == "OSBAG", "OSBAG convertts to OSBAG"

    def test_ferguson_wf(self):
        subject = station_code_from_duids(["FNWF1"])

        assert subject == "FNWF", "Trims and strips numbers"
