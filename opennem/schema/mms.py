# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
"""
OpenNEM MMS Schemas
"""

from pydantic import BaseModel, ConfigDict, field_validator

from opennem.core.normalizers import normalize_duid, participant_name_filter


class MMSBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class MMSParticipant(MMSBase):
    code: str | None = None
    name: str
    country: str = "au"
    abn: str | None = None

    @classmethod
    @field_validator("code")
    @classmethod
    def code_clean(cls, v):
        return normalize_duid(v)

    @classmethod
    @field_validator("name")
    @classmethod
    def name_clean(cls, v):
        name = participant_name_filter(v)

        return name


class MMSStation(MMSBase):
    name: str
    network_id: str


class MMSFacility(MMSBase):
    code: str | None = None
    name: str

    @classmethod
    @field_validator("code")
    @classmethod
    def code_clean(cls, v):
        return normalize_duid(v)

    @classmethod
    @field_validator("network_name")
    @classmethod
    def network_name_isalpha(cls, v):
        assert type(v) is str, "must be string"

        return v

    @classmethod
    @field_validator("name")
    @classmethod
    def name_clean(cls, v):
        # todo auto-set name based on network_name
        name = participant_name_filter(v)

        return name
