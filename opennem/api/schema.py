from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from opennem.schema.opennem import (
    FueltechSchema,
    RevisionSchema,
    StationSchema,
)


class ApiBase(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        use_enum_values = True
        arbitrary_types_allowed = True
        validate_assignment = True


# all records have an id
class RecordBase(BaseModel):
    id: int


class StationResponse(BaseModel):
    success: bool = False
    record_num: int
    records: Optional[List[StationSchema]]


class StationModificationTypes(str, Enum):
    approve = "approve"


class StationModification(ApiBase):
    comment: Optional[str] = Field(None)
    modification: StationModificationTypes


class RevisionModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class RevisionModification(ApiBase):
    comment: Optional[str] = Field(None)
    modification: RevisionModificationTypes


class UpdateResponse(ApiBase):
    success: bool = False
    record: Optional[RecordBase]


class FueltechResponse(ApiBase):
    success: bool = True

    records: List[FueltechSchema]


class RevisionUpdate(ApiBase):
    pass


class StationIDListLocation(ApiBase):
    state: str
    country: str = "au"


class StationIDList(ApiBase):
    id: int
    name: str
    location: StationIDListLocation
