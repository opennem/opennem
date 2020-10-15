from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field

from opennem.api.schema import ApiBase
from opennem.core.dispatch_type import DispatchType
from opennem.schema.opennem import (
    FacilityStatusSchema,
    FueltechSchema,
    NetworkSchema,
)


class FacilityRecord(ApiBase):
    id: int

    network: NetworkSchema

    fueltech: Optional[FueltechSchema]

    status: Optional[FacilityStatusSchema]

    station_id: Optional[int]

    # @TODO no longer optional
    code: str = ""

    dispatch_type: DispatchType
    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    network_region: Optional[str]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    created_by: Optional[str]
    created_at: Optional[datetime]

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]


class FacilityUpdateResponse(ApiBase):
    success: bool = False
    record: FacilityRecord


class FacilityResponse(ApiBase):
    success: bool = False
    record_num: int
    records: Optional[List[FacilityRecord]]


class FacilityModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class FacilityModification(ApiBase):
    comment: Optional[str] = Field(None)
    modification: FacilityModificationTypes

