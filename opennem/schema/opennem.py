# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, validator
from shapely import geometry

from opennem.api.photo.schema import Photo
from opennem.api.stats.schema import OpennemData
from opennem.api.weather.schema import WeatherStation
from opennem.core.dispatch_type import DispatchType
from opennem.core.networks import datetime_add_network_timezone
from opennem.core.normalizers import clean_capacity, string_to_title
from opennem.schema.response import ResponseStatus
from opennem.utils.dates import chop_datetime_microseconds, optionally_parse_string_datetime
from opennem.utils.version import get_version

from .core import BaseConfig
from .network import NetworkNEM, NetworkSchema

logger = logging.getLogger(__name__)


class OpennemBaseSchema(BaseConfig):
    version: str = get_version()
    created_at: datetime = chop_datetime_microseconds(datetime.now())
    response_status: ResponseStatus = ResponseStatus.OK

    _version_fromstr = validator("created_at", allow_reuse=True, pre=True)(
        optionally_parse_string_datetime
    )


class OpennemBaseDataSchema(OpennemBaseSchema):
    total_records: Optional[int]


class OpennemErrorSchema(OpennemBaseSchema):
    response_status = ResponseStatus.ERROR
    detail: str


class FueltechSchema(BaseConfig):
    code: str
    label: Optional[str]
    renewable: Optional[bool]


class FacilityStatusSchema(BaseConfig):
    code: str
    label: Optional[str]


class ParticipantSchema(BaseConfig):
    id: int
    code: Optional[str]
    name: str
    network_name: Optional[str] = None
    network_code: Optional[str] = None
    country: Optional[str] = None
    abn: Optional[str] = None


class StationBaseSchema(BaseConfig):
    id: int


class FacilityBaseSchema(BaseConfig):
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


class ScadaReading(Tuple[datetime, Optional[float]]):
    pass

    id: Optional[int]

    network: NetworkSchema = NetworkNEM

    fueltech: Optional[FueltechSchema]

    status: Optional[FacilityStatusSchema]

    station_id: Optional[int]

    # @TODO no longer optional
    code: Optional[str] = ""

    scada_power: Optional[OpennemData]

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    network_region: Optional[str]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    emissions_factor_co2: Optional[float]

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]

    @validator("capacity_registered")
    def _clean_capacity_regisered(cls, value: Union[str, int, float]) -> Optional[float]:
        _v = clean_capacity(value)

        if isinstance(value, float):
            _v = round(value, 2)

        return _v

    @validator("emissions_factor_co2")
    def _clean_emissions_factor_co2(cls, value: Union[str, int, float]) -> Optional[float]:
        _v = clean_capacity(value)

        return _v


class WeatherStationNearest(BaseModel):
    code: str
    distance: float


class LocationSchema(BaseConfig):
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
    geom: Optional[Any] = None
    boundary: Optional[Any]

    lat: Optional[float]
    lng: Optional[float]

    @validator("address1")
    def clean_address(cls, value: str) -> str:
        return string_to_title(value)

    @validator("address2")
    def clean_address2(cls, value: str) -> str:
        return string_to_title(value)

    @validator("locality")
    def clean_locality(cls, value: str) -> str:
        return string_to_title(value)

    @validator("state")
    def state_upper(cls, value: str) -> Optional[str]:
        if value:
            return value.upper()

        return None

    @validator("postcode")
    def clean_postcode(cls, value: str) -> Optional[str]:
        if value:
            return value.strip()

        return None

    @validator("geom", pre=True)
    def parse_geom(cls, value: WKBElement) -> Any:

        if value:
            return geometry.mapping(to_shape(value))

    @validator("boundary", pre=True)
    def parse_boundary(cls, value: WKBElement) -> Any:

        if value:
            return geometry.mapping(to_shape(value))


def as_nem_timezone(dt: datetime) -> Optional[datetime]:
    """Cast date with network NEM timezone

    @TODO should catch errors before getting to this point
    """
    if dt:
        return datetime_add_network_timezone(dt, NetworkNEM)

    return None


def _flatten_linked_object(value: Union[str, Dict, object]) -> str:
    if not value:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict) and "code" in value:
        return value["code"]

    if isinstance(value, object) and hasattr(value, "code"):
        return value.code  # type: ignore

    raise TypeError("Could not flatten no value or invalid")


class FacilityOutputSchema(BaseConfig):
    id: Optional[int]

    network: str = "NEM"

    fueltech: Optional[str]

    status: Optional[str]

    # @TODO no longer optional
    code: Optional[str] = ""

    scada_power: Optional[OpennemData]

    dispatch_type: DispatchType = DispatchType.GENERATOR

    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    network_region: Optional[str]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    emissions_factor_co2: Optional[float]

    data_first_seen: Optional[datetime]
    data_last_seen: Optional[datetime]

    _seen_dates_tz = validator("data_first_seen", "data_last_seen", pre=True, allow_reuse=True)(
        as_nem_timezone
    )

    _flatten_embedded = validator("network", "fueltech", "status", pre=True, allow_reuse=True)(
        _flatten_linked_object
    )

    @validator("capacity_registered")
    def _clean_capacity_regisered(cls, value: Union[str, float, int]) -> Optional[float]:
        _v = clean_capacity(value)

        if isinstance(value, float):
            _v = round(value, 2)

        return _v

    @validator("emissions_factor_co2")
    def _clean_emissions_factor_co2(cls, value: Union[str, float, int]) -> Optional[float]:
        _v = clean_capacity(value)

        return _v


class FacilitySchema(BaseConfig):
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

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    network_region: Optional[str]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    emissions_factor_co2: Optional[float]

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]

    @validator("capacity_registered")
    def _clean_capacity_regisered(cls, value):
        value = clean_capacity(value)

        if isinstance(value, float):
            value = round(value, 2)

        return value

    @validator("emissions_factor_co2")
    def _clean_emissions_factor_co2(cls, value):
        value = clean_capacity(value)

        return value


class FacilityImportSchema(BaseConfig):
    id: Optional[int]

    network: NetworkSchema = NetworkNEM
    network_id: Optional[str]

    fueltech: Optional[FueltechSchema]
    fueltech_id: Optional[str]

    status: Optional[FacilityStatusSchema]
    status_id: Optional[str]

    # @TODO no longer optional
    code: Optional[str] = ""

    scada_power: Optional[OpennemData]

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: Optional[float]

    registered: Optional[datetime]
    deregistered: Optional[datetime]

    network_region: Optional[str]

    unit_id: Optional[int]
    unit_number: Optional[int]
    unit_alias: Optional[str]
    unit_capacity: Optional[float]

    emissions_factor_co2: Optional[float]

    approved: bool = False
    approved_by: Optional[str]
    approved_at: Optional[datetime]


class StationImportSchema(BaseConfig):
    id: Optional[int]

    code: str

    participant: Optional[ParticipantSchema] = None

    facilities: Optional[List[FacilityImportSchema]] = []

    photos: Optional[List[Photo]]

    name: Optional[str]

    # Original network fields
    network_name: Optional[str]

    location: LocationSchema = LocationSchema()

    network: Optional[str] = None

    approved: bool = True

    description: Optional[str]
    wikipedia_link: Optional[str]
    wikidata_id: Optional[str]
    website_url: Optional[str]


class StationSchema(BaseConfig):
    id: Optional[int]

    code: str

    participant: Optional[ParticipantSchema] = None

    facilities: Optional[List[FacilitySchema]] = []

    photos: Optional[List[Photo]]

    name: Optional[str]

    # Original network fields
    network_name: Optional[str]

    location: LocationSchema = LocationSchema()

    network: Optional[str] = None

    approved: bool = True

    data_first_seen: datetime
    data_last_seen: datetime

    description: Optional[str]
    wikipedia_link: Optional[str]
    wikidata_id: Optional[str]
    website_url: Optional[str]


class StationOutputSchema(BaseConfig):
    id: int

    code: str

    participant: Optional[ParticipantSchema] = None

    facilities: Optional[List[FacilityOutputSchema]] = []

    photos: Optional[List[Photo]]

    name: Optional[str]

    # Original network fields
    network_name: Optional[str]

    location: LocationSchema = LocationSchema()

    network: Optional[str] = None

    description: Optional[str]
    wikipedia_link: Optional[str]
    wikidata_id: Optional[str]
    website_url: Optional[str]
