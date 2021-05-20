from typing import List, Optional

from opennem.api.schema import ApiBase
from opennem.schema.opennem import OpennemBaseDataSchema


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


class LocationResponse(OpennemBaseDataSchema):
    record: LocationSchema


class LocationsResponse(OpennemBaseDataSchema):
    data: List[LocationSchema]
