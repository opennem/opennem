"""
Schemas for stats
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator
from xlrd.xldate import xldate_as_datetime

from opennem.schema.field_types import RoundedFloat2


class StatTypes(Enum):
    CPI = "CPI"
    Inflation = "INFLATION"

    def __str__(self) -> str:
        return f"{self.value}"


class StatDatabase(BaseModel):
    stat_date: datetime
    country: str = "au"
    stat_type: StatTypes
    value: RoundedFloat2

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, use_enum_values=True)


class StatsSet(BaseModel):
    name: str
    source_url: str
    fetched_date: datetime
    stats: list[StatDatabase]


class AUCpiData(BaseModel):
    quarter_date: datetime
    cpi_value: RoundedFloat2

    @field_validator("quarter_date", mode="before")
    @classmethod
    def parse_quarter_date(cls, value) -> datetime:
        v = xldate_as_datetime(value, 0)

        if not v or not isinstance(v, datetime):
            raise ValueError("Invalid CPI quarter")

        return v


class AUInflationData(BaseModel):
    quarter_date: datetime
    inflation_value: RoundedFloat2

    @field_validator("quarter_date", mode="before")
    @classmethod
    def parse_quarter_date(cls, value) -> datetime:
        v = xldate_as_datetime(value, 0)

        if not v or not isinstance(v, datetime):
            raise ValueError("Invalid CPI quarter")

        return v
