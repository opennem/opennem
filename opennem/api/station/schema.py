from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field

from opennem.api.schema import ApiBase


class StationIDListLocation(ApiBase):
    state: str
    country: str = "au"


class StationIDList(ApiBase):
    id: int
    name: str
    location: StationIDListLocation


class StationRecord(ApiBase):
    id: int

    code: str

    name: Optional[str]

    # Original network fields
    network_name: Optional[str]

    location_id: Optional[int]

    approved: bool = False

    # network: Optional[NetworkSchema] = None

    description: Optional[str]
    wikipedia_link: Optional[str]
    wikidata_id: Optional[str]

    created_by: Optional[str]
    created_at: Optional[datetime]


class StationUpdateResponse(ApiBase):
    success: bool = False
    record: StationRecord


class StationResponse(ApiBase):
    success: bool = False
    record_num: int
    records: Optional[List[StationRecord]]


class StationModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class StationModification(ApiBase):
    comment: Optional[str] = Field(None)
    modification: StationModificationTypes
