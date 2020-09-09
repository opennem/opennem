"""
    Set of stations


"""
from collections import UserList
from typing import List, Optional

from opennem.exporter.encoders import opennem_serialize
from opennem.schema.opennem import StationSchema


def _str_comp(subject: str, value: str) -> bool:
    return subject.trim().lower() == value.trim().lower()


class StationSet(UserList):
    """

    """

    # def __init__(self,):
    #     pass

    def get(self, key: int) -> Optional[StationSchema]:
        _entry = list(filter(lambda s: s.id == key, self.data))

        if not _entry or len(_entry) == 0:
            return None

        return _entry.pop()

    def get_by(self, **kwargs):
        print(kwargs)

    def get_name(self, name: str) -> List[StationSchema]:
        _entries = list(filter(lambda s: _str_comp(s.name, name), self.data))

        return _entries

    def get_code(self, code: str) -> Optional[StationSchema]:
        _entries = list(filter(lambda s: s.code == code, self.data))

        if not _entries or len(_entries) == 0:
            return None

        if len(_entries) > 1:
            raise Exception("More than one station with a code")

        return _entries.pop()

    def one(self):
        pass

    def add(self, station: StationSchema):
        if not station.code:
            raise Exception("Require a station code")

        _key = station.code

        if self.get_code(_key):
            raise Exception("Duplicate code {}".format(_key))

        self.data.append(station)

        return self

    def add_dict(self, station_dict: dict):
        station = StationSchema(**station_dict)

        self.add(station)

    def as_list(self) -> List[StationSchema]:
        return self.data

    def json(self, indent=None):
        _data = [i.dict() for i in self.data]

        return opennem_serialize(_data, indent=indent)

    @property
    def length(self) -> int:
        return len(self.data)
