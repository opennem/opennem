from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, validator

from opennem.api.photo.schema import Photo
from opennem.api.stats.schema import OpennemData
from opennem.api.weather.schema import WeatherStation
from opennem.core.dispatch_type import DispatchType
from opennem.core.normalizers import (  # clean_numbers,; station_name_cleaner,
    clean_capacity,
    normalize_string,
)
from opennem.core.oid import get_ocode, get_oid

from .core import BaseConfig


class OpennemBaseSchema(BaseConfig):

    created_by: Optional[str]
    created_at: Optional[datetime] = datetime.now()


class FueltechSchema(BaseConfig):
    code: str
    label: str
    renewable: bool


from pytz import timezone


class NetworkSchema(BaseConfig):
    code: str
    country: str
    label: str
    timezone: str
    interval_size: int

    def get_timezone(self) -> timezone:
        return timezone(self.timezone)


NetworkNEM = NetworkSchema(
    code="NEM",
    label="NEM",
    country="au",
    timezone="Australia/Sydney",
    interval_size=5,
)
NetworkWEM = NetworkSchema(
    code="WEM",
    label="WEM",
    country="au",
    timezone="Australia/Perth",
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


class ScadaReading(Tuple[datetime, Optional[float]]):
    pass


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


class WeatherStationNearest(BaseModel):
    code: str
    distance: float


class LocationSchema(OpennemBaseSchema):
    id: Optional[int]

    weather_station: Optional[WeatherStation]
    weather_nearest: Optional[WeatherStationNearest]

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

    photos: Optional[List[Photo]]

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

    network: Optional[NetworkSchema] = None

    description: Optional[str]
    wikipedia_link: Optional[str]
    wikidata_id: Optional[str]

