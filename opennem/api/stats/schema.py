from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, validator

from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeIntervalAPI, TimePeriodAPI
from opennem.utils.timezone import get_current_timezone


class ScadaInterval(object):
    date: datetime
    value: Optional[float]

    def __init__(self, date: datetime, value: Optional[float] = None):
        self.date = date
        self.value = value


class ScadaReading(Tuple[datetime, Optional[float]]):
    pass


class UnitScadaReading(BaseModel):
    code: str
    data: List[ScadaReading]


class StationScadaReading(BaseModel):
    code: str
    facilities: Dict[str, UnitScadaReading]


class OpennemDataHistory(BaseConfig):
    start: Union[datetime, date]
    last: Union[datetime, date]
    interval: str
    data: List[Optional[float]]

    @validator("data")
    def validate_data(cls, data_value):
        data_value = list(map(lambda x: round(x, 2) if x else 0.0, data_value))

        return data_value


class OpennemData(BaseConfig):
    id: Optional[str]
    type: Optional[str]
    region: Optional[str]
    fuel_tech: Optional[str]

    network: Optional[str]
    data_type: str
    code: str = ""
    units: str

    interval: TimeIntervalAPI
    period: Optional[TimePeriodAPI]

    history: OpennemDataHistory


class OpennemDataSet(BaseConfig):
    type: Optional[str]
    network: Optional[str]
    code: str
    region: Optional[str]
    created_at: Optional[datetime]

    data: List[OpennemData]


class DataQueryResult(BaseConfig):
    interval: datetime
    result: Union[float, int, None, Decimal]
    group_by: Optional[str]


class ScadaDateRange(BaseConfig):
    start: datetime
    end: datetime
    network: Optional[NetworkSchema]

    def _get_value_localized(self, field_name: str = "start"):
        timezone = get_current_timezone()
        date_aware = getattr(self, field_name)

        if self.network:
            timezone = self.network.get_timezone()

        date_aware = date_aware.astimezone(timezone)

        return date_aware

    def get_start(self):
        return self._get_value_localized("start")

    def get_end(self):
        return self._get_value_localized("end")

    def get_start_sql(self, as_date: bool = False) -> str:
        return "'{}'".format(
            self.get_start() if not as_date else self.get_start().date()
        )

    def get_end_sql(self, as_date: bool = False) -> str:
        return "'{}'".format(
            self.get_end() if not as_date else self.get_end().date()
        )
