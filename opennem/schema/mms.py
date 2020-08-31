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


class MMSBase(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True


class MMSParticipant(MMSBase):
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


class MMSStation(MMSBase):
    name: str
    network_id: str


class MMSFacility(MMSBase):
    code: Optional[str]
    name: str

    @classmethod
    @validator("code")
    def code_clean(cls, v):
        return normalize_duid(v)

    @classmethod
    @validator("network_name")
    def network_name_isalpha(cls, v):
        assert type(v) is str, "must be string"
        # assert v.isalpha(), "must be alpha: {}".format(v)

        return v

    @classmethod
    @validator("name")
    def name_clean(cls, v):
        # todo auto-set name based on network_name
        name = participant_name_filter(v)

        return name
