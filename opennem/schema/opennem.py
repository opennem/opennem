from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, validator

from opennem.core.dispatch_type import DispatchType
from opennem.core.oid import get_ocode, get_oid

from opennem.core.normalizers import (  # clean_numbers,; station_name_cleaner,
    clean_capacity,
    normalize_string,
)


class BaseConfig(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

        arbitrary_types_allowed = True
        validate_assignment = True

        json_encoders = {
            # datetime: lambda v: v.isotime(),
            # Decimal: lambda v: float(v),
        }


class OpennemBaseSchema(BaseConfig):

    created_by: Optional[str]
    created_at: Optional[datetime] = datetime.now()

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        use_enum_values = True
        arbitrary_types_allowed = True
        validate_assignment = True

        json_encoders = {}


class FueltechSchema(BaseConfig):
    code: str
    label: str
    renewable: bool


class NetworkSchema(BaseConfig):
    code: str
    country: str
    label: str
    timezone: str
    interval_size: int


NetworkNEM = NetworkSchema(
    code="NEM",
    label="NEM",
    country="au",
    timezone="Australia/Perth",
    interval_size=5,
)
NetworkWEM = NetworkSchema(
    code="WEM",
    label="WEM",
    country="au",
    timezone="Australia/Sydney",
    interval_size=30,
)


class FacilityStatusSchema(BaseConfig):
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


class GeoPoint(BaseModel):
    lat: float
    lng: float


class GeoBoundary(BaseModel):
    pass


class RecordTypes(str, Enum):
    station = "station"
    facility = "facility"
    location = "location"
    revision = "revision"


class RevisionSchema(OpennemBaseSchema):
    id: int

    changes: Dict[str, Union[str, int, float, bool, None]] = {}
    previous: Optional[Dict[str, Union[str, int, float, bool]]] = {}

    parent_id: Optional[int]
    parent_type: Optional[str]
    station_owner_id: Optional[int]
    station_owner_name: Optional[str]
    station_owner_code: Optional[str]

    is_update: bool = False

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    approved_comment: Optional[str]

    discarded: bool = False
    discarded_by: Optional[str]
    discarded_at: Optional[datetime]

    # station_id: Optional[int]
    # facility_id: Optional[int]
    # location_id: Optional[int]

    # @validator("changes")
    # def validate_data(cls, data_value):
    #     if not data_value:
    #         return data_value

    #     for field_value in data_value.values():
    #         assert isinstance(
    #             field_value, (int, str, bool, float)
    #         ), "Data values have to be int, str, bool or float"


class ScadaReading(Tuple[datetime, Optional[float]]):
    pass


class OpennemDataHistory(BaseConfig):
    start: datetime
    last: datetime
    interval: int
    data: List[float]


class OpennemData(BaseConfig):
    region: str = ""
    network: str
    data_type: str
    units: str
    history: OpennemDataHistory


class FacilitySchema(OpennemBaseSchema):
    id: Optional[int]

    network: NetworkSchema = NetworkNEM

    fueltech: Optional[FueltechSchema]

    status: Optional[FacilityStatusSchema]

    station_id: Optional[int]

    # @TODO no longer optional
    code: Optional[str] = ""

    scada_power: Optional[OpennemData]

    # revisions: Optional[List[RevisionSchema]] = []
    # revision_ids: Optional[List[int]] = []

    dispatch_type: DispatchType = "GENERATOR"

    active: bool = True

    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    network_region: Optional[str]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]

    @validator("capacity_registered")
    def _clean_capacity_regisered(cls, value):
        value = clean_capacity(value)

        return value


class LocationSchema(OpennemBaseSchema):
    id: Optional[int]

    address1: Optional[str] = ""
    address2: Optional[str] = ""
    locality: Optional[str] = ""
    state: Optional[str] = ""
    postcode: Optional[str] = ""
    country: Optional[str] = "au"

    # Geo fields
    # place_id: Optional[str]
    geocode_approved: bool = False
    geocode_skip: bool = False
    geocode_processed_at: Optional[datetime] = None
    geocode_by: Optional[str]
    # geom: Optional[WKBElement] = None
    # boundary: Optional[WKBElement] = None

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
    def state_upper(cls, value: str) -> Optional[str]:
        if value:
            return value.upper()

    @validator("postcode")
    def clean_postcode(cls, value: str) -> Optional[str]:
        if value:
            return value.strip()

    @property
    def geom(self) -> Optional[str]:
        if not self.lng or not self.lat:
            return None

        geom = "SRID=4326;POINT({} {})".format(self.lng, self.lat,)

        return geom


class StationSchema(OpennemBaseSchema):
    id: Optional[int]

    participant: Optional[ParticipantSchema] = None
    participant_id: Optional[str]

    facilities: Optional[List[FacilitySchema]] = []

    # history: Optional[List[__self__]]

    # revisions: Optional[List[RevisionSchema]]

    code: str

    name: Optional[str]

    # Original network fields
    network_name: Optional[str]

    location: LocationSchema = LocationSchema()
    location_id: Optional[int]

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]

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
