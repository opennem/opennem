from opennem.api.schema import ApiBase
from opennem.schema.opennem import OpennemBaseDataSchema


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


class LocationResponse(OpennemBaseDataSchema):
    record: LocationSchema


class LocationsResponse(OpennemBaseDataSchema):
    data: list[LocationSchema]
