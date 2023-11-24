from datetime import datetime
from enum import Enum

from pydantic import Field

from opennem.api.schema import ApiBase
from opennem.core.dispatch_type import DispatchType
from opennem.schema.opennem import FacilityStatusSchema, FueltechSchema


class NetworkRecord(ApiBase):
    code: str


class FacilityRecord(ApiBase):
    id: int

    network: NetworkRecord

    fueltech: FueltechSchema | None = None

    status: FacilityStatusSchema | None = None

    station_id: int | None = None

    # @TODO no longer optional
    code: str = ""

    dispatch_type: DispatchType
    capacity_registered: float | None = None

    registered: datetime | None = None
    deregistered: datetime | None = None

    network_region: str | None = None

    unit_id: int | None = None
    unit_number: int | None = None
    unit_alias: str | None = None
    unit_capacity: float | None = None

    created_by: str | None = None
    created_at: datetime | None = None

    approved: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None


class FacilityUpdateResponse(ApiBase):
    success: bool = False
    record: FacilityRecord


class FacilityResponse(ApiBase):
    success: bool = False
    record_num: int
    records: list[FacilityRecord] | None = None


class FacilityModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class FacilityModification(ApiBase):
    comment: str | None = Field(None)
    modification: FacilityModificationTypes
