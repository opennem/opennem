from datetime import datetime

from pydantic import BaseModel

from opennem.schema.unit import UnitSchema


class FacilityPhotoOutputSchema(BaseModel):
    """Facility photo output schema"""

    url: str
    caption: str | None = None
    attribution: str | None = None


class CMSFacilityLocationSchema(BaseModel):
    """Facility location schema"""

    _type: str
    lat: float | None = None
    lng: float | None = None


class FacilitySchema(BaseModel):
    """Station output schema"""

    code: str
    name: str
    network_id: str
    network_region: str
    website: str | None = None
    description: str | None = None
    wikipedia: str | None = None
    photos: list[FacilityPhotoOutputSchema] | None = None
    location: CMSFacilityLocationSchema | None = None
    units: list[UnitSchema]

    # Sanity fields
    updated_at: datetime | None = None
