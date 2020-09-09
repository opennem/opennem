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

        arbitrary_types_allowed = True
        validate_assignment = True


# all records have a code
class RecordBase(BaseModel):
    code: str


class StationResponse(BaseModel):
    success: bool = False
    record_num: int
    records: Optional[List[StationSchema]]


class RevisionApproval(ApiBase):
    comment: Optional[str] = Field(None)


class UpdateResponse(ApiBase):
    success: bool = False
    record: Optional[RecordBase]


class FueltechResponse(ApiBase):
    success: bool = True

    records: List[FueltechSchema]
