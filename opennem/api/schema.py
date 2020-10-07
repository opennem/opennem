from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ApiBase(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        use_enum_values = True
        arbitrary_types_allowed = True
        validate_assignment = True


class UpdateResponse(BaseModel):
    success: bool = True
    records: List = []


class FueltechResponse(ApiBase):
    success: bool = True

    # @TODO fix circular references
    # records: List[FueltechSchema]

