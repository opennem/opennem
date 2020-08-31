# pylint: disable=no-self-argument, no-self-use
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from geoalchemy2.elements import WKBElement
from pydantic import BaseModel, validator

from opennem.core.dispatch_type import DispatchType
from opennem.core.facilitystatus import (
    map_aemo_facility_status,
    parse_facility_status,
)
from opennem.core.normalizers import (
    clean_capacity,
    clean_numbers,
    normalize_string,
    station_name_cleaner,
)
from opennem.core.oid import get_ocode, get_oid
from opennem.exporter.encoders import OpenNEMJSONEncoder


class OpennemBaseSchema(BaseModel):

    created_by: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

        #
        arbitrary_types_allowed = True
        # validate_assignment = True

        json_encoders = {}

        # def json_dumps(self):
        #     print("json", self.__values__)
        #     return json.dumps(self.__values__, cls=OpenNEMJSONEncoder,)


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


class FacilitySchema(OpennemBaseSchema):
    network: NetworkSchema = NetworkSchema(
        code="NEM", country="au", label="NEM"
    )
    network_code: str = "NEM"

    fueltech: Optional[FueltechSchema]

    status: FacilityStatusSchema

    # @TODO no longer optional
    code: Optional[str] = ""

    dispatch_type: DispatchType = "GENERATOR"

    active: bool = True

    capacity_registered: Optional[float]
    capacity_maximum: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    network_region: str

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    @validator("capacity_registered")
    def clean_capacity_regisered(cls, value):
        # value = clean_capacity(value)

        return value

    @validator("capacity_maximum")
    def clean_capacity_maximum(cls, value):
        value = clean_capacity(value)

        return value


class StationSchema(OpennemBaseSchema):
    id: int

    participant: Optional[ParticipantSchema] = None
    participant_id: Optional[str]

    facilities: List[FacilitySchema] = []

    code: str

    name: str

    address1: Optional[str] = ""
    address2: Optional[str] = ""
    locality: Optional[str] = ""
    state: Optional[str] = ""
    postcode: Optional[str] = ""

    # Original network fields
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

    # geo fields
    lat: Optional[float]
    lng: Optional[float]

    @validator("address1")
    def clean_address(cls, value):
        return normalize_string(value)

    @validator("address2")
    def clean_address2(cls, value):
        return normalize_string(value)

    @validator("locality")
    def clean_locality(cls, value):
        return normalize_string(value)

    @validator("state")
    def state_upper(cls, value: str) -> str:
        return value.upper()

    @validator("postcode")
    def clean_postcode(cls, value: str) -> str:
        return value.strip()

    # @validator("createdat")
    def created_at_exists(cls, value: Optional[datetime]) -> datetime:
        dt = None

        return dt

    @property
    def capacity_registered(self) -> Optional[int]:
        """
            This is the sum of registered capacities for all units for
            this station

        """
        cap_reg = None

        for fac in self.facilities:
            if (
                fac.capacity_registered
                and type(fac.capacity_registered) in [int, float, Decimal]
                and fac.status
                and fac.status.code
                in ["operating", "committed", "commissioning"]
                and fac.dispatch_type == DispatchType.GENERATOR
                and fac.active
            ):
                if not cap_reg:
                    cap_reg = 0

                cap_reg += fac.capacity_registered

        if cap_reg:
            cap_reg = round(cap_reg, 2)

        return cap_reg

    @property
    def capacity_aggregate(self) -> Optional[int]:
        """
            This is the sum of aggregate capacities for all units

        """
        cap_agg = None

        for fac in self.facilities:
            if (
                fac.capacity_aggregate
                and type(fac.capacity_aggregate) in [int, float, Decimal]
                and fac.status
                and fac.status.code
                in ["operating", "committed", "commissioning"]
                and fac.dispatch_type == DispatchType.GENERATOR
                and fac.active
            ):
                if not cap_agg:
                    cap_agg = 0

                cap_agg += fac.capacity_aggregate

        if cap_agg:
            cap_agg = round(cap_agg, 2)

        return cap_agg

    def oid(self) -> str:
        return get_oid(self)

    def ocode(self) -> str:
        return get_ocode(self)


class StationSubmission(BaseModel):
    name: str
    network_id: str

    class Config:
        orm_mode = True
