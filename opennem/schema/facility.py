from typing import Optional

from pydantic import BaseModel, ValidationError, validator

from opennem.core.normalizers import (
    clean_capacity,
    is_number,
    normalize_duid,
    normalize_string,
    participant_name_filter,
    station_name_cleaner,
)

from .opennem import OpennemBaseModel


class OpennemFacility(OpennemBaseModel):
    code: Optional[str]
    name: str
    network_name: str

    @classmethod
    @validator("code")
    def code_clean(cls, v):
        return normalize_duid(v)

    @classmethod
    @validator("network_name")
    def network_name_isalpha(cls, v):
        assert type(v) is str, "must be string"
        return v
