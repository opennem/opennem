"""
OpenNEM v2 formatted output exports as Pydantic schemas

"""

from datetime import date, datetime
from typing import List, Optional, Tuple, Union

from pydantic import validator

# from opennem.api.stats.schema import data_validate
from opennem.schema.core import BaseConfig
from opennem.utils.interval import get_human_interval

# from pydantic import validator


def strip_timezone(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None)


def fix_v2_date(date_str: str) -> str:
    return date_str.replace("+1000", "+10:00")


class OpennemDataHistoryV2(BaseConfig):
    start: Union[datetime, date]
    last: Union[datetime, date]
    interval: str
    data: List[Optional[float]]

    # validators
    _start_date = validator("start", allow_reuse=True, pre=True)(fix_v2_date)
    _end_date = validator("last", allow_reuse=True, pre=True)(fix_v2_date)

    def values(self) -> List[Tuple[date, Optional[float]]]:
        interval_obj = get_human_interval(self.interval)
        dt = self.start

        # return as list rather than generate
        xy_values = []

        if self.interval in ["5m", "30m", "1h"]:
            dt = dt + interval_obj

        for v in self.data:
            if isinstance(dt, datetime):
                dt = strip_timezone(dt)

            xy_values.append((dt, v))
            dt = dt + interval_obj

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
