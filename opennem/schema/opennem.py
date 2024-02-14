# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
import logging
from datetime import datetime
from enum import Enum
from typing import Any

from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, field_validator, validator
from shapely import geometry

from opennem.api.stats.schema import OpennemData
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
    total_records: int | None = None


class OpennemErrorSchema(OpennemBaseSchema):
    response_status: ResponseStatus = ResponseStatus.ERROR
    error: str
    success: bool = False


class FueltechSchema(BaseConfig):
    code: str
    label: str | None = None
    renewable: bool | None = None


class FacilityStatusSchema(BaseConfig):
    code: str
    label: str | None = None


class ParticipantSchema(BaseConfig):
    id: int
    code: str | None = None
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


class ScadaReading(tuple[datetime, float | None]):
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

    @field_validator("capacity_registered")
    @classmethod
    def _clean_capacity_regisered(cls, value: str | int | float) -> float | None:
        _v = clean_capacity(value)

        if isinstance(value, float):
            _v = round(value, 2)

        return _v

    @field_validator("emissions_factor_co2")
    @classmethod
    def _clean_emissions_factor_co2(cls, value: str | int | float) -> float | None:
        _v = clean_capacity(value)

        return _v


class WeatherStationNearest(BaseModel):
    code: str
    distance: float


class LocationSchema(BaseConfig):
    id: int | None = None

    # weather_station: WeatherStation | None
    # weather_nearest: WeatherStationNearest | None

    address1: str | None = None
    address2: str | None = None
    locality: str | None = None
    state: str | None = None
    postcode: str | None = None
    country: str = "au"

    # Geo fields
    # place_id: Optional[str]
    geocode_approved: bool = False
    # geocode_skip: bool = False
    geocode_processed_at: datetime | None = None
    geocode_by: str | None = None
    geom: dict[str, str | tuple] | None = None
    boundary: Any | None = None

    lat: float | None = None
    lng: float | None = None

    @field_validator("address1")
    @classmethod
    def clean_address(cls, value: str) -> str:
        return string_to_title(value)

    @field_validator("address2")
    @classmethod
    def clean_address2(cls, value: str) -> str:
        return string_to_title(value)

    @field_validator("locality")
    @classmethod
    def clean_locality(cls, value: str) -> str:
        return string_to_title(value)

    @field_validator("state")
    @classmethod
    def state_upper(cls, value: str) -> str | None:
        if value:
            return value.upper()

        return None

    @field_validator("postcode")
    @classmethod
    def clean_postcode(cls, value: str) -> str | None:
        if value:
            return value.strip()

        return None

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("geom", pre=True, always=True, allow_reuse=True)
    def parse_geom(cls, value: WKBElement) -> Any:
        if value:
            mapping = geometry.mapping(to_shape(value))
            return mapping

    @field_validator("boundary", mode="before")
    @classmethod
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
    id: int | None = None

    network: str = "NEM"

    fueltech: str | None = None

    status: str | None = None

    # @TODO no longer optional
    code: str | None = ""

    scada_power: OpennemData | None = None

    dispatch_type: DispatchType = DispatchType.GENERATOR

    capacity_registered: float | None = None

    registered: datetime | None = None
    deregistered: datetime | None = None

    network_region: str | None = None

    unit_id: int | None = None
    unit_number: int | None = None
    unit_alias: str | None = None
    unit_capacity: float | None = None

    emissions_factor_co2: float | None = None

    data_first_seen: datetime | None = None
    data_last_seen: datetime | None = None

    _seen_dates_tz = validator("data_first_seen", "data_last_seen", pre=True, allow_reuse=True)(as_nem_timezone)

    _flatten_embedded = validator("network", "fueltech", "status", pre=True, allow_reuse=True)(_flatten_linked_object)

    @field_validator("capacity_registered")
    @classmethod
    def _clean_capacity_regisered(cls, value: str | float | int) -> float | None:
        _v = clean_capacity(value)

        if isinstance(value, float):
            _v = round(value, 2)

        return _v

    @field_validator("emissions_factor_co2")
    @classmethod
    def _clean_emissions_factor_co2(cls, value: str | float | int) -> float | None:
        _v = clean_capacity(value)

        return _v


class FacilitySchema(BaseConfig):
    id: int | None = None

    network: NetworkSchema = NetworkNEM

    fueltech: FueltechSchema | None = None

    status: FacilityStatusSchema | None = None

    station_id: int | None = None

    # @TODO no longer optional
    code: str | None = ""

    scada_power: OpennemData | None = None

    # revisions: Optional[List[RevisionSchema]] = []
    # revision_ids: Optional[List[int]] = []

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: float | None = None

    registered: datetime | None = None
    deregistered: datetime | None = None

    network_region: str | None = None

    unit_id: int | None = None
    unit_number: int | None = None
    unit_alias: str | None = None
    unit_capacity: float | None = None

    emissions_factor_co2: float | None = None

    approved: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None

    @field_validator("capacity_registered")
    @classmethod
    def _clean_capacity_regisered(cls, value):
        value = clean_capacity(value)

        if isinstance(value, float):
            value = round(value, 2)

        return value

    @field_validator("emissions_factor_co2")
    @classmethod
    def _clean_emissions_factor_co2(cls, value):
        value = clean_capacity(value)

        return value


class FacilityImportSchema(BaseConfig):
    id: int | None = None

    network: NetworkSchema = NetworkNEM
    network_id: str | None = None

    fueltech: FueltechSchema | None = None
    fueltech_id: str | None = None

    status: FacilityStatusSchema | None = None
    status_id: str | None = None

    # @TODO no longer optional
    code: str | None = ""

    scada_power: OpennemData | None = None

    dispatch_type: DispatchType = DispatchType.GENERATOR

    active: bool = True

    capacity_registered: float | None = None

    registered: datetime | None = None
    deregistered: datetime | None = None

    network_region: str | None = None

    unit_id: int | None = None
    unit_number: int | None = None
    unit_alias: str | None = None
    unit_capacity: float | None = None

    emissions_factor_co2: float | None = None
    emission_factor_source: str | None = None

    approved: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None


class StationImportSchema(BaseConfig):
    id: int | None = None

    code: str

    participant: ParticipantSchema | None = None

    facilities: list[FacilityImportSchema] | None = []

    name: str | None = None

    # Original network fields
    network_name: str | None = None

    location: LocationSchema = LocationSchema()

    network: str | None = None

    approved: bool = True

    description: str | None = None
    wikipedia_link: str | None = None
    wikidata_id: str | None = None
    website_url: str | None = None


class StationSchema(BaseConfig):
    id: int | None = None

    code: str

    participant: ParticipantSchema | None = None

    facilities: list[FacilitySchema] | None = []

    name: str | None = None

    # Original network fields
    network_name: str | None = None

    location: LocationSchema = LocationSchema()

    network: str | None = None

    approved: bool = True

    data_first_seen: datetime
    data_last_seen: datetime

    description: str | None = None
    wikipedia_link: str | None = None
    wikidata_id: str | None = None
    website_url: str | None = None


class StationOutputSchema(BaseConfig):
    id: int

    code: str

    participant: ParticipantSchema | None = None

    facilities: list[FacilityOutputSchema] | None = []

    name: str | None = None

    # Original network fields
    network_name: str | None = None

    location: LocationSchema | None = None

    network: str | None = None

    description: str | None = None
    wikipedia_link: str | None = None
    wikidata_id: str | None = None
    website_url: str | None = None
