from pydantic import BaseModel, validator

from opennem.core.normalizers import normalize_whitespace


class SchemaBase(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True


class FacilitySchema(SchemaBase):
    network_region: str
    status: str
    duid: str
    name: str
    fueltech: str | None = None
    capacity: float | None = None


class StationSchema(SchemaBase):
    name: str
    code: str | None = None
    state: str | None = None
    facilities: list[FacilitySchema] = []

    @classmethod
    @validator("name")
    def name_clean(cls, v):
        name = normalize_whitespace(v)

        return name

    @classmethod
    @validator("state")
    def state_clean(cls, v):
        state = v.upper()

        return state
