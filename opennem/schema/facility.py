from datetime import datetime

from pydantic import BaseModel, Field

from opennem.schema.field_types import RoundedFloat6
from opennem.schema.unit import UnitSchema


class FacilityPhotoOutputSchema(BaseModel):
    """Facility photo output schema"""

    url: str
    url_source: str | None = None
    caption: str | None = None
    attribution: str | None = None
    alt: str | None = None
    width: int | None = None
    height: int | None = None


class FacilityLocationSchema(BaseModel):
    """Facility location schema"""

    type: str = Field(default="Point", alias="_type")
    lat: RoundedFloat6 | None = None
    lng: RoundedFloat6 | None = None


class FacilityOwnerSchema(BaseModel):
    """Facility owner schema"""

    name: str
    website: str | None = None
    wikipedia: str | None = None


class FacilitySchema(BaseModel):
    """Station output schema"""

    code: str
    name: str
    network_id: str
    network_region: str
    website: str | None = None
    description: str | None = None
    wikipedia: str | None = None
    osm_way_id: str | None = None  # OpenStreetMap Way ID
    photos: list[FacilityPhotoOutputSchema] | None = None
    owners: list[FacilityOwnerSchema] | None = None
    location: FacilityLocationSchema | None = None
    units: list[UnitSchema]

    # Sanity fields
    updated_at: datetime | None = None
    cms_id: str | None = Field(None, alias="_id")
