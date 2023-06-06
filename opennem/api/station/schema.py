from datetime import datetime
from enum import Enum

from pydantic import Field

from opennem.api.schema import ApiBase
from opennem.core.dispatch_type import DispatchType
from opennem.schema.opennem import OpennemBaseDataSchema


class FueltechSchema(ApiBase):
    code: str
    label: str | None
    renewable: bool | None


class FacilityStatusSchema(ApiBase):
    code: str
    label: str | None


class FacilitySchema(ApiBase):
    id: int | None

    # network: NetworkSchema

    fueltech: FueltechSchema | None

    status: FacilityStatusSchema | None

    station_id: int | None

    # @TODO no longer optional
    code: str = ""

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: float | None

    registered: datetime | None
    deregistered: datetime | None
    expected_closure_date: datetime | None
    expected_closure_year: int | None

    network_region: str | None

    unit_id: int | None
    unit_number: int | None
    unit_alias: str | None
    unit_capacity: float | None

    emissions_factor_co2: float | None

    approved: bool = False
    approved_by: str | None
    approved_at: datetime | None


class LocationSchema(ApiBase):
    id: int | None

    address1: str | None = ""
    address2: str | None = ""
    locality: str | None = ""
    state: str | None = ""
    postcode: str | None = ""
    country: str | None = "au"

    # Geo fields
    # place_id: Optional[str]
    # geocode_approved: bool = False
    # geocode_skip: bool = False
    # geocode_processed_at: Optional[datetime] = None
    # geocode_by: Optional[str]
    # geom: Optional[Any] = None
    # boundary: Optional[Any]

    lat: float | None
    lng: float | None


class StationRecord(ApiBase):
    id: int

    code: str

    name: str | None

    # Original network fields
    # network_name: str | None

    # location: Optional[LocationSchema]
    location_id: int

    facilities: list[FacilitySchema]

    approved: bool = False

    # network: Optional[NetworkSchema] = None

    description: str | None
    wikipedia_link: str | None
    wikidata_id: str | None

    created_by: str | None
    created_at: datetime | None


class StationResponse(OpennemBaseDataSchema):
    record: StationRecord


class StationsResponse(OpennemBaseDataSchema):
    data: list[StationRecord]


class StationUpdateResponse(ApiBase):
    success: bool = False
    record: StationRecord


class StationModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class StationModification(ApiBase):
    comment: str | None = Field(None)
    modification: StationModificationTypes
