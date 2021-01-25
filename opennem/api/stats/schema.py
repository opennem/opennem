from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, List, Optional, Union

from pydantic import validator

from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeIntervalAPI, TimePeriodAPI
from opennem.settings import settings
from opennem.utils.numbers import sigfig_compact
from opennem.utils.timezone import get_current_timezone


def chop_microseconds(dt: datetime) -> datetime:
    return dt - timedelta(microseconds=dt.microsecond)


def optionaly_lowercase_string(value: str) -> str:
    """Read from settings if we want output schema string
    values to be lowercased or not and perform"""
    if settings.schema_output_lowercase_strings:
        value = value.lower()

    return value


def number_output(n: Union[float, int, None]) -> Optional[float]:
    """Format numbers for data series outputs"""
    if n is None:
        return None

    if n == 0:
        return 0

    return sigfig_compact(n)


def get_data_id(
    network: NetworkSchema,
) -> str:
    """Method to build the data id for a stat export"""
    id_components = []

    if settings.schema_output_id_country:
        id_components.append(network.country)

    id_str = ".".join([i.lower() for i in id_components if i])

    return id_str


class OpennemDataHistory(BaseConfig):
    start: Union[datetime, date]
    last: Union[datetime, date]
    interval: Optional[str]
    data: List[Optional[float]]

    @validator("data")
    def validate_data(cls, data_value):
        data_value = list(
            map(
                number_output,
                data_value,
            )
        )

        return data_value


class OpennemData(BaseConfig):
    id: Optional[str]
    type: Optional[str]
    fuel_tech: Optional[str]

    network: Optional[str]
    region: Optional[str]
    data_type: str
    code: str = ""
    units: str

    interval: Optional[TimeIntervalAPI]
    period: Optional[TimePeriodAPI]

    history: OpennemDataHistory
    forecast: Optional[OpennemDataHistory]

    # validators
    _id_lowercase = validator("id", allow_reuse=True, pre=True)(optionaly_lowercase_string)
    _network_lowercase = validator("network", allow_reuse=True, pre=True)(
        optionaly_lowercase_string
    )
    _region_lowercase = validator("region", allow_reuse=True, pre=True)(optionaly_lowercase_string)
    _code_lowercase = validator("code", allow_reuse=True, pre=True)(optionaly_lowercase_string)


class OpennemDataSet(BaseConfig):
    type: Optional[str]
    version: Optional[str]
    network: Optional[str]
    code: str
    region: Optional[str]
    created_at: Optional[datetime]

    data: List[OpennemData]

    def append_set(self, subject_set: Optional[OpennemDataSet] = None):
        if not subject_set:
            return None

        if not subject_set.data:
            return None

        if not isinstance(subject_set.data, list):
            return None

        if len(subject_set.data):
            self.data += subject_set.data

        return None

    # validators
    _created_at_trim = validator("created_at", allow_reuse=True, pre=True)(chop_microseconds)
    _network_lowercase = validator("network", allow_reuse=True, pre=True)(
        optionaly_lowercase_string
    )
    _region_lowercase = validator("region", allow_reuse=True, pre=True)(optionaly_lowercase_string)
    _code_lowercase = validator("code", allow_reuse=True, pre=True)(optionaly_lowercase_string)


class RegionFlowResult(BaseConfig):
    interval: datetime
    flow_from: str
    flow_to: str
    generated: Optional[float]


class RegionFlowEmissionsResult(BaseConfig):
    interval: datetime
    flow_from: str
    flow_to: str
    energy: float
    flow_from_emissions: Optional[float]
    flow_to_emissions: Optional[float]


class DataQueryResult(BaseConfig):
    interval: datetime
    result: Union[float, int, None, Decimal]
    group_by: Optional[str]


class ScadaDateRange(BaseConfig):
    start: datetime
    end: datetime
    network: Optional[NetworkSchema]

    def _get_value_localized(self, field_name: str = "start") -> Any:
        timezone = get_current_timezone()
        date_aware = getattr(self, field_name)

        if self.network:
            timezone = self.network.get_timezone()

        date_aware = date_aware.astimezone(timezone)

        return date_aware

    def get_start_year(self) -> int:
        return self.start.year

    def get_start(self) -> datetime:
        return self._get_value_localized("start")

    def get_end(self) -> datetime:
        return self._get_value_localized("end")

    def get_start_sql(self, as_date: bool = False) -> str:
        return "'{}'".format(self.get_start() if not as_date else self.get_start().date())

    def get_end_sql(self, as_date: bool = False) -> str:
        return "'{}'".format(self.get_end() if not as_date else self.get_end().date())
