"""
Schemas for stats
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from xlrd.xldate import xldate_as_datetime

from opennem.core.normalizers import clean_float


class StatTypes(Enum):
    CPI = "CPI"
    Inflation = "INFLATION"

    def __str__(self) -> str:
        return f"{self.value}"


class StatDatabase(BaseModel):
    stat_date: datetime
    country: str = "au"
    stat_type: StatTypes
    value: float

    @field_validator("value", mode="before")
    @classmethod
    def parse_cpi_value(cls, value: Any) -> float:
        v = clean_float(value)

        if not v:
            raise ValueError("No Value")

        return v

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, use_enum_values=True)


class StatsSet(BaseModel):
    name: str
    source_url: str
    fetched_date: datetime
    stats: list[StatDatabase]


class AUCpiData(BaseModel):
    quarter_date: datetime
    cpi_value: float

    @field_validator("quarter_date", mode="before")
    @classmethod
    def parse_quarter_date(cls, value) -> datetime:
        v = xldate_as_datetime(value, 0)

        if not v or not isinstance(v, datetime):
            raise ValueError("Invalid CPI quarter")

        return v

    @field_validator("cpi_value", mode="before")
    @classmethod
    def parse_cpi_value(cls, value: Any) -> float:
        v = clean_float(value)

        if not v:
            raise ValueError("No CPI Value")

        return v


class AUInflationData(BaseModel):
    quarter_date: datetime
    inflation_value: float

    @field_validator("quarter_date", mode="before")
    @classmethod
    def parse_quarter_date(cls, value) -> datetime:
        v = xldate_as_datetime(value, 0)

        if not v or not isinstance(v, datetime):
            raise ValueError("Invalid CPI quarter")

        return v

    @field_validator("inflation_value", mode="before")
    @classmethod
    def parse_cpi_value(cls, value: Any) -> float:
        v = clean_float(value)

        if not v:
            raise ValueError("No inflation Value")

        return v
