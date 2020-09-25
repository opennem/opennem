from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from opennem.schema.opennem import (
    FacilitySchema,
    FueltechSchema,
    LocationSchema,
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


class RevisionModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class RevisionModification(ApiBase):
    comment: Optional[str] = Field(None)
    modification: RevisionModificationTypes


class RevisionModificationResponse(ApiBase):
    success: bool = False
    record: RevisionSchema
    target: Optional[Union[FacilitySchema, StationSchema, LocationSchema]]


class FueltechResponse(ApiBase):
    success: bool = True

    records: List[FueltechSchema]


class RevisionUpdate(ApiBase):
    pass

