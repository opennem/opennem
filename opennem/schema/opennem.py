import json
from datetime import datetime
from typing import List, Optional, Union

from geoalchemy2.elements import WKBElement
from pydantic import BaseModel

from opennem.core.dispatch_type import DispatchType
from opennem.exporter.encoders import OpenNEMJSONEncoder


class OpennemBaseSchema(BaseModel):

    created_by: Optional[str]
    updated_by: Optional[str]

    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

        #
        arbitrary_types_allowed = True
        # validate_assignment = True

        json_encoders = {}

        def json_dumps(self):
            print("json", self.__values__)
            return json.dumps(self.__values__, cls=OpenNEMJSONEncoder,)


class FueltechSchema(OpennemBaseSchema):
    code: str
    label: str
    renewable: bool


class NetworkSchema(OpennemBaseSchema):
    code: str
    country: str
    label: str


class FacilityStatusSchema(OpennemBaseSchema):
    code: str
    label: str


class ParticipantSchema(OpennemBaseSchema):
    id: int
    code: Optional[str]
    name: str
    network_name: Optional[str] = None
    network_code: Optional[str] = None
    country: Optional[str] = None
    abn: Optional[str] = None


class StationBaseSchema(OpennemBaseSchema):
    id: int


class FacilityBaseSchema(OpennemBaseSchema):
    id: int


class FacilitySchema(FacilityBaseSchema):

    participant: ParticipantSchema
    participant_id: Optional[str]

    fueltech: FueltechSchema
    fueltech_id: Optional[str]

    status: FacilityStatusSchema
    status_id: Optional[str]

    station: StationBaseSchema
    station_id: int

    code: str

    network_code: str
    network_region: Optional[str]
    network_name: Optional[str]

    active: bool = True

    dispatch_type: DispatchType

    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    # virtual methods
    capacity_aggregate: Optional[int]
    duid: str
    oid: str
    ocode: str
    status_label: Optional[str]
    fueltech_label: Optional[str]


class StationSchema(StationBaseSchema):
    network: NetworkSchema
    network_id: str

    participant: Optional[ParticipantSchema] = None
    participant_id: Optional[str]

    # facilities: List[FacilitySchema] = []

    code: Optional[str] = None
    name: Optional[str] = None

    address1: Optional[str] = ""
    address2: Optional[str] = ""
    locality: Optional[str] = ""
    state: Optional[str] = ""
    postcode: Optional[str] = ""

    # Original network fields
    network_code: Optional[str]
    network_name: Optional[str]

    # Geo fields
    # place_id: Optional[str]
    geocode_approved: bool = False
    geocode_skip: bool = False
    geocode_processed_at: Optional[datetime] = None
    geocode_by: Optional[str]
    # geom: Optional[WKBElement] = None
    # boundary: Optional[WKBElement] = None

    # virtual methods
    capacity_aggregate: Optional[int]
    oid: str
    ocode: str
    lat: Optional[float]
    lng: Optional[float]


class StationSubmission(BaseModel):
    name: str
    network_id: str

    class Config:
        orm_mode = True
