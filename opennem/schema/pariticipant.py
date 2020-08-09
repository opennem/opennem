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


class OpennemParticipant(OpennemBaseModel):
    code: Optional[str]
    name: str
    country: str = "au"
    abn: Optional[str]

    @classmethod
    @validator("code")
    def code_clean(cls, v):
        return normalize_duid(v)

    @classmethod
    @validator("name")
    def name_clean(cls, v):
        name = participant_name_filter(v)

        return name
