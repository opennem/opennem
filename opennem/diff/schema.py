from typing import List, Optional

from pydantic import BaseModel


class SchemaBase(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True


class FacilitySchema(SchemaBase):
    network_region: str
    status: str
    duid: str
    fueltech: Optional[str] = None
    capacity: Optional[float] = None


class StationSchema(SchemaBase):
    name: str
    code: Optional[str] = None
    state: Optional[str] = None
    facilities: List[FacilitySchema] = []
