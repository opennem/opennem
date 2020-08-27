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

from .opennem import OpennemBaseSchema


class OpennemParticipant(OpennemBaseSchema):
    code: Optional[str]
    name: str
    country: str = "au"
    abn: Optional[str]

    @validator("code")
    def code_clean(self, v):
        return normalize_duid(v)

    @validator("name")
    def name_clean(cls, value):
        name = participant_name_filter(value)

        return name
