from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from opennem.api.facility.schema import FacilityRecord
from opennem.api.schema import ApiBase
from opennem.api.station.schema import StationRecord

# from opennem.schema.core import BaseConfig
from opennem.schema.opennem import LocationSchema, RevisionSchema


class UpdateResponse(BaseModel):
    success: bool = True
    records: List = []


class RevisionModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class RevisionModification(ApiBase):
    comment: Optional[str] = Field(None)
    modification: RevisionModificationTypes


class RevisionModificationResponse(ApiBase):
    success: bool = False
    record: RevisionSchema
    target: Optional[Union[FacilityRecord, StationRecord, LocationSchema]]

