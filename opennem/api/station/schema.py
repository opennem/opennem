from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field

from opennem.api.schema import ApiBase
from opennem.core.dispatch_type import DispatchType
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.opennem import OpennemBaseDataSchema


class FueltechSchema(ApiBase):
    code: str
    label: Optional[str]
    renewable: Optional[bool]


class FacilityStatusSchema(ApiBase):
    code: str
    label: Optional[str]


class FacilitySchema(ApiBase):
    id: Optional[int]

    network: NetworkSchema = NetworkNEM

    fueltech: Optional[FueltechSchema]

    status: Optional[FacilityStatusSchema]

    station_id: Optional[int]

    # @TODO no longer optional
    code: str = ""

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]
    expected_closure_date: Optional[datetime]
    expected_closure_year: Optional[int]

    network_region: Optional[str]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    emissions_factor_co2: Optional[float]

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]


class LocationSchema(ApiBase):
    id: Optional[int]

    address1: Optional[str] = ""
    address2: Optional[str] = ""
    locality: Optional[str] = ""
    state: Optional[str] = ""
    postcode: Optional[str] = ""
    country: Optional[str] = "au"

    # Geo fields
    # place_id: Optional[str]
    # geocode_approved: bool = False
    # geocode_skip: bool = False
    # geocode_processed_at: Optional[datetime] = None
    # geocode_by: Optional[str]
    # geom: Optional[Any] = None
    # boundary: Optional[Any]

    lat: Optional[float]
    lng: Optional[float]


class StationRecord(ApiBase):
    id: int

    code: str

    name: Optional[str]

    # Original network fields
    network_name: Optional[str]

    # location: Optional[LocationSchema]
    location_id: int

    facilities: List[FacilitySchema]

    approved: bool = False

    # network: Optional[NetworkSchema] = None

    description: Optional[str]
    wikipedia_link: Optional[str]
    wikidata_id: Optional[str]

    created_by: Optional[str]
    created_at: Optional[datetime]


class StationResponse(OpennemBaseDataSchema):
    record: StationRecord


class StationsResponse(OpennemBaseDataSchema):
    data: List[StationRecord]


class StationUpdateResponse(ApiBase):
    success: bool = False
    record: StationRecord


class StationModificationTypes(str, Enum):
    approve = "approve"
    reject = "reject"


class StationModification(ApiBase):
    comment: Optional[str] = Field(None)
    modification: StationModificationTypes
