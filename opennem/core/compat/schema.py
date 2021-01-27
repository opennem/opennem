"""
OpenNEM v2 formatted output exports as Pydantic schemas

"""

from datetime import date, datetime
from typing import List, Optional, Tuple, Union

# from opennem.api.stats.schema import data_validate
from opennem.schema.core import BaseConfig
from opennem.utils.interval import get_human_interval

# from pydantic import validator


class OpennemDataHistoryV2(BaseConfig):
    start: Union[datetime, date]
    last: Union[datetime, date]
    interval: str
    data: List[Optional[float]]

    # validators
    # _data_valid = validator("data", allow_reuse=True, pre=True)(data_validate)

    def values(self) -> List[Tuple[datetime, float]]:
        interval_obj = get_human_interval(self.interval)
        dt = self.start

        # return as list rather than generate
        xy_values = []

        for v in self.data:
            dt = dt + interval_obj
            xy_values.append((dt, v))

        return xy_values


class OpennemDataV2(BaseConfig):
    id: str
    region: str
    type: Optional[str]
    units: str
    fuel_tech: Optional[str]

    history: OpennemDataHistoryV2
    forecast: Optional[OpennemDataHistoryV2]


class OpennemDataSetV2(BaseConfig):
    version: str = "v2"
    data: List[OpennemDataV2]

    def get_id(self, id: str) -> Optional[OpennemDataV2]:
        _ds = list(filter(lambda x: x.id == id, self.data))

        if len(_ds) < 1:
            return None

        return _ds.pop()
