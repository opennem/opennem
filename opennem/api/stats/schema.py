from __future__ import annotations

import logging
import math
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional, Union
from xml.dom import ValidationErr
from zoneinfo import ZoneInfo

import pydantic
from datedelta import datedelta
from pydantic import validator

from opennem.api.time import human_to_interval
from opennem.core.compat.utils import translate_id_v3_to_v2
from opennem.core.fueltechs import map_v3_fueltech
from opennem.core.validators.data import validate_data_outputs
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema
from opennem.schema.response import ResponseStatus
from opennem.schema.time import TimeIntervalAPI, TimePeriodAPI
from opennem.settings import settings
from opennem.utils.dates import chop_datetime_microseconds
from opennem.utils.http import http
from opennem.utils.interval import get_human_interval
from opennem.utils.numbers import sigfig_compact

ValidNumber = Union[float, int, None, Decimal]


logger = logging.getLogger("opennem.stats.schema")


def optionaly_lowercase_string(value: str) -> str:
    """Read from settings if we want output schema string
    values to be lowercased or not and perform"""

    if not value:
        raise ValueError("Require a value to lowercase")

    if settings.schema_output_lowercase_strings:
        value = value.lower()

    return value


def number_output(n: Union[float, int, None]) -> Optional[Union[float, int, None, Decimal]]:
    """Format numbers for data series outputs"""
    if n is None:
        return None

    if n == 0:
        return 0

    if math.isnan(n):
        return None

    return sigfig_compact(n)


def format_number_series(values: list[ValidNumber]) -> list[ValidNumber]:
    """Validate and format list of numeric data values"""
    return list(
        map(
            number_output,  # type: ignore
            values,
        )
    )


def optionally_parse_string_datetime(
    value: Optional[Union[str, datetime, date]] = None
) -> Optional[Union[str, datetime, date]]:
    if not value:
        return value

    if isinstance(value, str):
        return datetime.fromisoformat(value)

    return value


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
    start: datetime
    last: datetime
    interval: str
    data: list[ValidNumber] = pydantic.Field(..., description="Data values")

    # validators
    _data_format = validator("data", allow_reuse=True, pre=True)(format_number_series)

    @validator("data", pre=True, always=True)
    def validate_data(
        cls, field_value: list[ValidNumber], values: dict[str, datetime | str | list[ValidNumber]]
    ) -> list[ValidNumber]:
        if not field_value:
            return field_value

        interval: str | None = values.get("interval", None)
        start: datetime | None = values.get("start", None)
        last: datetime | None = values.get("last", None)

        if not interval or not start or not last:
            raise ValidationErr("Missing interval or start or last for data validation")

        if not isinstance(start, datetime):
            raise ValidationErr(f"Start is not a datetime: {start}")

        if not isinstance(last, datetime):
            raise ValidationErr(f"Last is not a datetime: {last}")

        logger.debug(f"{len(field_value)} values at {interval} interval from {start} to {last}")

        interval_obj = get_human_interval(interval)

        validation_output = validate_data_outputs(field_value, interval_obj, start, last)

        if not validation_output:
            raise ValidationErr(f"Data validation failed: {validation_output}")

        return field_value

    def get_date(self, dt: date) -> float | Decimal | None:
        """Get value for a specific date"""
        _values = self.values()
        _get_value = list(filter(lambda x: x[0].date() == dt, _values))

        if not _get_value:
            return None

        return _get_value.pop()[1]

    def get_interval(self) -> timedelta | datedelta:
        return get_human_interval(self.interval)

    def values(self) -> list[tuple[datetime, ValidNumber]]:
        interval_obj = get_human_interval(self.interval)
        dt = self.start

        # return as list rather than generate as optimization
        timeseries_data = []

        for v in self.data:
            timeseries_data.append((dt, v))
            dt = dt + interval_obj

        assert validate_data_outputs(self.data, self.get_interval(), self.start, self.last) is True

        return timeseries_data


class OpennemData(BaseConfig):
    id: Optional[str]
    type: Optional[str]
    fuel_tech: Optional[str]

    network: Optional[str]
    region: Optional[str]
    data_type: str
    code: Optional[str]
    units: str

    interval: Optional[TimeIntervalAPI]
    period: Optional[TimePeriodAPI]

    history: OpennemDataHistory
    forecast: Optional[OpennemDataHistory]

    x_capacity_at_present: Optional[float]

    # validators

    # conveniance methods
    def id_v2(self) -> Optional[str]:
        if self.id:
            return translate_id_v3_to_v2(self.id)

        return None

    def fueltech_v2(self) -> Optional[str]:
        if self.fuel_tech:
            return map_v3_fueltech(self.fuel_tech)

        return None


class OpennemDataSet(BaseConfig):
    type: Optional[str]
    response_status: ResponseStatus = ResponseStatus.OK
    version: Optional[str]
    network: Optional[str]
    code: Optional[str]
    region: Optional[str]
    created_at: Optional[datetime]

    data: list[OpennemData] = []

    # Properties
    @property
    def ids(self) -> list[str]:
        """Return a list of data ids in this data set"""
        id_list = [i.id for i in self.data if i.id and isinstance(i.id, str)]

        return id_list

    # Methods
    def append_set(self, subject_set: Optional[OpennemDataSet] = None) -> None:
        if not subject_set:
            return None

        if not subject_set.data:
            return None

        if not isinstance(subject_set.data, list):
            return None

        if len(subject_set.data):
            self.data += subject_set.data

        return None

    def get_id(self, id: str) -> Optional[OpennemData]:
        _ds = list(filter(lambda x: x.id == id, self.data))

        if len(_ds) < 1:
            return None

        return _ds.pop()

    # Validators
    # pylint: disable=no-self-argument
    @validator("data", pre=True, allow_reuse=True)
    def validate_data_unique(cls, value: list[OpennemData], **kwargs) -> list[OpennemData]:
        """Validate the data being set to make sure there are no duplicate ids"""
        _id_values = [i.id for i in value]

        if len(_id_values) != len(set(_id_values)):
            # find the ids that are not unique
            _msg = ""
            _id_duplicates = [
                item for item, count in Counter(_id_values).items() if count > 1 and isinstance(item, str)
            ]

            if _id_duplicates:
                _duplicate_ids = ", ".join(_id_duplicates)
                _msg = f"{len(_id_values)} ids and {len(_duplicate_ids)} duplicates: {_duplicate_ids} "

            raise ValueError(f"OpennemDataSet has duplicate id{'s' if len(_id_duplicates) > 1 else ''}: {_msg}")

        return sorted(value, key=lambda x: x.id)  # type: ignore

    _version_fromstr = validator("created_at", allow_reuse=True, pre=True)(optionally_parse_string_datetime)

    _created_at_trim = validator("created_at", allow_reuse=True, pre=True)(chop_datetime_microseconds)
    _network_lowercase = validator("network", allow_reuse=True, pre=True)(optionaly_lowercase_string)


class RegionFlowResult(BaseConfig):
    interval: datetime
    flow_from: str
    flow_to: str
    generated: Optional[float]
    flow_from_energy: Optional[float]
    flow_to_energy: Optional[float]


class RegionFlowEmissionsResult(BaseConfig):
    interval: datetime
    flow_from: str
    flow_to: str
    energy: Optional[float]
    flow_from_emissions: Optional[float]
    flow_to_emissions: Optional[float]
    flow_from_intensity: Optional[float]
    flow_to_intensity: Optional[float]


class DataQueryResult(BaseConfig):
    interval: datetime
    result: Union[float, int, None, Decimal]
    group_by: Optional[str]


class ScadaDateRange(BaseConfig):
    start: datetime
    end: datetime
    network: Optional[NetworkSchema]

    def _get_value_localized(self, field_name: str = "start") -> Any:
        timezone: ZoneInfo | str = settings.timezone  # type: ignore
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


def load_opennem_dataset_from_file(file_path: str | Path) -> OpennemDataSet:
    """
    Reads the stored tableset fixture path and returns an OpennemDataSet
    """
    data_set = pydantic.parse_file_as(path=str(file_path), type_=OpennemDataSet)

    return data_set


def load_opennem_dataset_from_url(url: str) -> OpennemDataSet:
    """
    Reads an OpenNEM URL and returns an OpennemDataSet
    """
    response = http.get(url)

    if not response.ok:
        raise Exception(f"Could not download from {url}: {response.status_code}")

    data_set = pydantic.parse_obj_as(obj=response.json(), type_=OpennemDataSet)

    return data_set
