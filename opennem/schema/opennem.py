# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional

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

    _version_fromstr = validator("created_at", allow_reuse=True, pre=True)(optionally_parse_string_datetime)


class OpennemBaseDataSchema(OpennemBaseSchema):
    total_records: int | None


class OpennemErrorSchema(OpennemBaseSchema):
    response_status = ResponseStatus.ERROR
    detail: str


class FueltechSchema(BaseConfig):
    code: str
    label: str | None
    renewable: bool | None


class FacilityStatusSchema(BaseConfig):
    code: str
    label: str | None


class ParticipantSchema(BaseConfig):
    id: int
    code: str | None
    name: str
    network_name: str | None = None
    network_code: str | None = None
    country: str | None = None
    abn: str | None = None


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


class ScadaReading(tuple[datetime, Optional[float]]):
    pass

    id: int | None

    network: NetworkSchema = NetworkNEM

    fueltech: FueltechSchema | None

    status: FacilityStatusSchema | None

    station_id: int | None

    # @TODO no longer optional
    code: str | None = ""

    scada_power: OpennemData | None

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: float | None

    registered: datetime | None
    deregistered: datetime | None

    network_region: str | None

    unit_id: int | None
    unit_number: int | None
    unit_alias: str | None
    unit_capacity: float | None

    emissions_factor_co2: float | None

    approved: bool = False
    approved_by: str | None
    approved_at: datetime | None

    @validator("capacity_registered")
    def _clean_capacity_regisered(cls, value: str | int | float) -> float | None:
        _v = clean_capacity(value)

        if isinstance(value, float):
            _v = round(value, 2)

        return _v

    @validator("emissions_factor_co2")
    def _clean_emissions_factor_co2(cls, value: str | int | float) -> float | None:
        _v = clean_capacity(value)

        return _v


class WeatherStationNearest(BaseModel):
    code: str
    distance: float


class LocationSchema(BaseConfig):
    id: int | None

    weather_station: WeatherStation | None
    weather_nearest: WeatherStationNearest | None

    address1: str | None = ""
    address2: str | None = ""
    locality: str | None = ""
    state: str | None = ""
    postcode: str | None = ""
    country: str | None = "au"

    # Geo fields
    # place_id: Optional[str]
    geocode_approved: bool = False
    geocode_skip: bool = False
    geocode_processed_at: datetime | None = None
    geocode_by: str | None
    geom: Any | None = None
    boundary: Any | None

    lat: float | None
    lng: float | None

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
    def state_upper(cls, value: str) -> str | None:
        if value:
            return value.upper()

        return None

    @validator("postcode")
    def clean_postcode(cls, value: str) -> str | None:
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


def as_nem_timezone(dt: datetime) -> datetime | None:
    """Cast date with network NEM timezone

    @TODO should catch errors before getting to this point
    """
    if dt:
        return datetime_add_network_timezone(dt, NetworkNEM)

    return None


def _flatten_linked_object(value: str | dict | object) -> str:
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
    id: int | None

    network: str = "NEM"

    fueltech: str | None

    status: str | None

    # @TODO no longer optional
    code: str | None = ""

    scada_power: OpennemData | None

    dispatch_type: DispatchType = DispatchType.GENERATOR

    capacity_registered: float | None

    registered: datetime | None
    deregistered: datetime | None

    network_region: str | None

    unit_id: int | None
    unit_number: int | None
    unit_alias: str | None
    unit_capacity: float | None

    emissions_factor_co2: float | None

    data_first_seen: datetime | None
    data_last_seen: datetime | None

    _seen_dates_tz = validator("data_first_seen", "data_last_seen", pre=True, allow_reuse=True)(as_nem_timezone)

    _flatten_embedded = validator("network", "fueltech", "status", pre=True, allow_reuse=True)(_flatten_linked_object)

    @validator("capacity_registered")
    def _clean_capacity_regisered(cls, value: str | float | int) -> float | None:
        _v = clean_capacity(value)

        if isinstance(value, float):
            _v = round(value, 2)

        return _v

    @validator("emissions_factor_co2")
    def _clean_emissions_factor_co2(cls, value: str | float | int) -> float | None:
        _v = clean_capacity(value)

        return _v


class FacilitySchema(BaseConfig):
    id: int | None

    network: NetworkSchema = NetworkNEM

    fueltech: FueltechSchema | None

    status: FacilityStatusSchema | None

    station_id: int | None

    # @TODO no longer optional
    code: str | None = ""

    scada_power: OpennemData | None

    # revisions: Optional[List[RevisionSchema]] = []
    # revision_ids: Optional[List[int]] = []

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: float | None

    registered: datetime | None
    deregistered: datetime | None

    network_region: str | None

    unit_id: int | None
    unit_number: int | None
    unit_alias: str | None
    unit_capacity: float | None

    emissions_factor_co2: float | None

    approved: bool = False
    approved_by: str | None
    approved_at: datetime | None

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
    id: int | None

    network: NetworkSchema = NetworkNEM
    network_id: str | None

    fueltech: FueltechSchema | None
    fueltech_id: str | None

    status: FacilityStatusSchema | None
    status_id: str | None

    # @TODO no longer optional
    code: str | None = ""

    scada_power: OpennemData | None

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: float | None

    registered: datetime | None
    deregistered: datetime | None

    network_region: str | None

    unit_id: int | None
    unit_number: int | None
    unit_alias: str | None
    unit_capacity: float | None

    emissions_factor_co2: float | None
    emission_factor_source: str | None

    approved: bool = False
    approved_by: str | None
    approved_at: datetime | None


class StationImportSchema(BaseConfig):
    id: int | None

    code: str

    participant: ParticipantSchema | None = None

    facilities: list[FacilityImportSchema] | None = []

    photos: list[Photo] | None

    name: str | None

    # Original network fields
    network_name: str | None

    location: LocationSchema = LocationSchema()

    network: str | None = None

    approved: bool = True

    description: str | None
    wikipedia_link: str | None
    wikidata_id: str | None
    website_url: str | None


class StationSchema(BaseConfig):
    id: int | None

    code: str

    participant: ParticipantSchema | None = None

    facilities: list[FacilitySchema] | None = []

    photos: list[Photo] | None

    name: str | None

    # Original network fields
    network_name: str | None

    location: LocationSchema = LocationSchema()

    network: str | None = None

    approved: bool = True

    data_first_seen: datetime
    data_last_seen: datetime

    description: str | None
    wikipedia_link: str | None
    wikidata_id: str | None
    website_url: str | None


class StationOutputSchema(BaseConfig):
    id: int

    code: str

    participant: ParticipantSchema | None = None

    facilities: list[FacilityOutputSchema] | None = []

    photos: list[Photo] | None

    name: str | None

    # Original network fields
    network_name: str | None

    location: LocationSchema = LocationSchema()

    network: str | None = None

    description: str | None
    wikipedia_link: str | None
    wikidata_id: str | None
    website_url: str | None
