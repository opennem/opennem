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


class Participant(BaseModel):
    # id: int = Optional[int]
    code: Optional[str]
    name: str
    network_name: str
    country: str = "au"
    abn: Optional[str]

    @validator("code")
    def code_clean(cls, v):
        return normalize_duid(v)

    @validator("network_name")
    def network_name_isalpha(cls, v):
        assert type(v) is str, "must be string"
        # assert v.isalpha(), "must be alpha: {}".format(v)

        return v

    @validator("name")
    def name_clean(cls, v):
        name = participant_name_filter(v)

        return name

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        # validate_assignment = True


class Station(BaseModel):
    id: int


class Station(BaseModel):
    id: int
