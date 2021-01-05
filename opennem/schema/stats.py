"""
Schemas for stats
"""

from datetime import datetime
from enum import Enum
from typing import Any, List

from pydantic import BaseModel
from pydantic.class_validators import validator
from xlrd.xldate import xldate_as_datetime

from opennem.core.normalizers import clean_float


class StatTypes(Enum):
    CPI = "CPI"
    Inflation = "INFLATION"

    def __str__(self) -> str:
        return "%s" % self.value


class StatDatabase(BaseModel):
    stat_date: datetime
    country: str = "au"
    stat_type: StatTypes
    value: float

    @validator("value", pre=True)
    def parse_cpi_value(cls, value: Any) -> float:
        v = clean_float(value)

        if not v:
            raise ValueError("No Value")

        return v

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        use_enum_values = True


class StatsSet(BaseModel):
    name: str
    source_url: str
    fetched_date: datetime
    stats: List[StatDatabase]


class AUCpiData(BaseModel):
    quarter_date: datetime
    cpi_value: float

    @validator("quarter_date", pre=True)
    def parse_quarter_date(cls, value) -> datetime:
        v = xldate_as_datetime(value, 0)

        if not v or not isinstance(v, datetime):
            raise ValueError("Invalid CPI quarter")

        return v

    @validator("cpi_value", pre=True)
    def parse_cpi_value(cls, value: Any) -> float:
        v = clean_float(value)

        if not v:
            raise ValueError("No CPI Value")

        return v


class AUInflationData(BaseModel):
    quarter_date: datetime
    inflation_value: float

    @validator("quarter_date", pre=True)
    def parse_quarter_date(cls, value) -> datetime:
        v = xldate_as_datetime(value, 0)

        if not v or not isinstance(v, datetime):
            raise ValueError("Invalid CPI quarter")

        return v

    @validator("inflation_value", pre=True)
    def parse_cpi_value(cls, value: Any) -> float:
        v = clean_float(value)

        if not v:
            raise ValueError("No inflation Value")

        return v
