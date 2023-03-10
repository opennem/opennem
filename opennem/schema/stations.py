"""
    Set of stations


"""
from collections import UserList
from typing import Self

from opennem.exporter.encoders import opennem_serialize
from opennem.schema.opennem import StationImportSchema


class StationSet(UserList):
    """Defines a set of stations"""

    def get(self, key: int) -> StationImportSchema | None:
        _entry = list(filter(lambda s: s.id == key, self.data))

        if not _entry or len(_entry) == 0:
            return None

        return _entry.pop()

    def get_code(self, code: str) -> StationImportSchema | None:
        _entries = list(filter(lambda s: s.code == code, self.data))

        if not _entries or len(_entries) == 0:
            return None

        if len(_entries) > 1:
            raise Exception("More than one station with a code")

        return _entries.pop()

    def add(self, station: StationImportSchema) -> Self:
        if not station.code:
            raise Exception("Require a station code")

        _key = station.code

        if self.get_code(_key):
            raise Exception(f"Duplicate code {_key}")

        self.data.append(station)

        return self

    def add_dict(self, station_dict: dict) -> None:
        station = StationImportSchema(**station_dict)

        self.add(station)

    def as_list(self) -> list[StationImportSchema]:
        return self.data

    def json(self, indent: int | None = None) -> str:
        _data = [i.dict() for i in self.data]

        return opennem_serialize(_data, indent=indent)

    @property
    def length(self) -> int:
        return len(self.data)
