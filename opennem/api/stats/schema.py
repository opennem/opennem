from __future__ import annotations

import logging
import math
import operator
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import pydantic
import requests
from datedelta import datedelta
from pydantic import PlainSerializer, ValidationError, field_validator

from opennem import settings
from opennem.core.feature_flags import get_list_of_enabled_features
from opennem.core.normalizers import cast_float_or_none
from opennem.core.validators.data import validate_data_outputs
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema
from opennem.schema.response import ResponseStatus
from opennem.schema.time import TimeIntervalAPI, TimePeriodAPI
from opennem.utils.dates import chop_datetime_microseconds
from opennem.utils.interval import get_human_interval
from opennem.utils.numbers import sigfig_compact

ValidNumber = float | int | Decimal
ValidNumberOrNull = ValidNumber | None


logger = logging.getLogger("opennem.stats.schema")


# flag to validate date ends in schema
VALIDATE_DATE_ENDS = False


def optionaly_lowercase_string(value: str) -> str:
    """Read from settings if we want output schema string
    values to be lowercased or not and perform"""

    if not value:
        raise ValueError("Require a value to lowercase")

    value = value.lower()

    return value


def number_output(n: float | int | None) -> float | int | None | Decimal | None:
    """Format numbers for data series outputs"""
    if n is None:
        return None

    if n == 0:
        return 0

    if math.isnan(n):
        return None

    return sigfig_compact(n)


def format_number_series(values: list[ValidNumberOrNull]) -> list[ValidNumberOrNull]:
    """Validate and format list of numeric data values"""
    return list(
        map(
            number_output,  # type: ignore
            values,
        )
    )


def optionally_parse_string_datetime(value: str | datetime | date | None = None) -> str | datetime | date | None:
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

    id_components.append(network.country)

    id_str = ".".join([i.lower() for i in id_components if i])

    return id_str


def validate_datetime_is_aware(value: datetime) -> datetime:
    """Validate that a datetime is timezone aware"""
    if not value.tzinfo:
        raise ValidationError("Datetime is not timezone aware")

    return value


class OpennemDataHistory(BaseConfig):
    start: datetime
    last: datetime
    interval: str
    data: Annotated[
        list[ValidNumberOrNull],
        PlainSerializer(lambda x: [cast_float_or_none(i) for i in x], return_type=list[float | None], when_used="json"),
    ] = pydantic.Field(..., description="Data values")

    def get_date(self, dt: date) -> ValidNumberOrNull:
        """Get value for a specific date"""
        _values = self.values()
        _get_value = list(filter(lambda x: x[0].date() == dt, _values))

        if not _get_value:
            return None

        return _get_value.pop()[1]

    def get_interval(self) -> timedelta | datedelta:
        return get_human_interval(self.interval)

    def values(self) -> list[tuple[datetime, ValidNumberOrNull]]:
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
    id: str | None = None
    type: str | None = None
    fuel_tech: str | None = None
    code: str | None = None

    network: str | None = None
    region: str | None = None
    data_type: str
    units: str

    interval: TimeIntervalAPI | None = None
    period: TimePeriodAPI | None = None

    history: OpennemDataHistory
    forecast: OpennemDataHistory | None = None

    x_capacity_at_present: float | None = None

    # validators


class OpennemDataSet(BaseConfig):
    type: str | None = None
    response_status: ResponseStatus = ResponseStatus.OK
    version: str | None = None
    network: str | None = None
    code: str | None = None
    region: str | None = None
    created_at: datetime | None = None
    feature_flags: list[str] = pydantic.Field(default_factory=get_list_of_enabled_features)
    messages: list[str] | None = None

    data: list[OpennemData] = []

    # Properties
    @property
    def ids(self) -> list[str]:
        """Return a list of data ids in this data set"""
        id_list = [i.id for i in self.data if i.id and isinstance(i.id, str)]

        return id_list

    # Methods
    def append_set(self, subject_set: OpennemDataSet | None = None) -> None:
        if not subject_set:
            return None

        if not subject_set.data:
            return None

        if not isinstance(subject_set.data, list):
            return None

        if len(subject_set.data):
            self.data += subject_set.data

        return None

    def get_id(self, id: str) -> OpennemData | None:
        _ds = list(filter(lambda x: x.id == id, self.data))

        if len(_ds) < 1:
            return None

        return _ds.pop()

    # Validators
    # pylint: disable=no-self-argument
    @field_validator("data", mode="before")
    @classmethod
    def validate_data_unique(cls, value: list[OpennemData], **kwargs) -> list[OpennemData]:
        """Validate the data being set to make sure there are no duplicate ids"""

        # this can be loaded with either a dict or with a model

        if not isinstance(value, list):
            return []

        if not value:
            return []

        if isinstance(value[0], OpennemData):
            _id_values = [i.id for i in value]
            sorting_key_method = lambda x: x.id  # noqa:E731
        elif isinstance(value[0], dict):
            _id_values = [i["id"] for i in value]
            sorting_key_method = operator.itemgetter("id")  # noqa:E731
        else:
            raise Exception("Not a valid value type")

        if len(_id_values) != len(set(_id_values)):
            # find the ids that are not unique
            _msg = ""
            _id_duplicates = [item for item, count in Counter(_id_values).items() if count > 1 and isinstance(item, str)]

            if _id_duplicates:
                _duplicate_ids = ", ".join(_id_duplicates)
                _msg = f"{len(_id_values)} ids and {len(_duplicate_ids)} duplicates: {_duplicate_ids} "

            raise ValueError(f"OpennemDataSet has duplicate id{"s" if len(_id_duplicates) > 1 else ""}: {_msg}")

        # validate end and start datetimes.
        # if they are not set, set them to the first and last values
        if VALIDATE_DATE_ENDS:
            max_date = max(
                [i.history.last for i in value if i.history and i.history.last and isinstance(i.history, OpennemDataHistory)]
            )
            min_date = min(
                [i.history.start for i in value if i.history and i.history.start and isinstance(i.history, OpennemDataHistory)]
            )

            for i in value:
                if not isinstance(i.history, OpennemDataHistory):
                    continue

                if i.history.last < max_date:
                    raise ValueError(f"Data set has invalid last date: {i.history.last}  {max_date}")

                if i.history.start < min_date:
                    raise ValueError(f"Data set has invalid start date: {i.history.start} {min_date}")

        return sorted(value, key=sorting_key_method)  # type: ignore

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, value):
        return optionally_parse_string_datetime(value)

    @field_validator("created_at")
    @classmethod
    def chop_datetime_microseconds(cls, value):
        return chop_datetime_microseconds(value)

    @field_validator("network")
    @classmethod
    def lowercase_network(cls, value):
        return optionaly_lowercase_string(value)


class RegionFlowResult(BaseConfig):
    interval: datetime
    flow_from: str
    flow_to: str
    generated: float | None = None
    flow_from_energy: float | None = None
    flow_to_energy: float | None = None


class RegionFlowEmissionsResult(BaseConfig):
    interval: datetime
    flow_from: str
    flow_to: str
    energy: float | None = None
    flow_from_emissions: float | None = None
    flow_to_emissions: float | None = None
    flow_from_intensity: float | None = None
    flow_to_intensity: float | None = None


class DataQueryResult(BaseConfig):
    interval: datetime
    result: float | None = None
    group_by: str | None = None


class ScadaDateRange(BaseConfig):
    start: datetime
    end: datetime
    network: NetworkSchema | None = None

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
        return f"'{self.get_start() if not as_date else self.get_start().date()}'"

    def get_end_sql(self, as_date: bool = False) -> str:
        return f"'{self.get_end() if not as_date else self.get_end().date()}'"


def load_opennem_dataset_from_file(file_path: str | Path) -> OpennemDataSet:
    """
    Reads the stored tableset fixture path and returns an OpennemDataSet
    """
    if not file_path.is_file():
        raise Exception(f"File does not exist: {file_path}")

    try:
        file_path = Path(file_path)
        json_data = file_path.read_text()
        return OpennemDataSet.model_validate_json(json_data)
    # return pydantic.parse_file_as(path=str(file_path), type_=OpennemDataSet)
    except Exception as e:
        raise Exception(f"Error loading file: {file_path} - {e}") from None


def load_opennem_dataset_from_url(url: str) -> OpennemDataSet:
    """
    Reads an OpenNEM URL and returns an OpennemDataSet
    """
    response = requests.get(url)

    if not response.ok:
        raise Exception(f"Could not download from {url}: {response.status_code}")

    data_set = pydantic.parse_obj_as(obj=response.json(), type_=OpennemDataSet)

    return data_set
