from datetime import date, datetime

from pydantic import BaseModel

from opennem.core.dispatch_type import DispatchType


class FacilityPhotoOutputSchema(BaseModel):
    """Facility photo output schema"""

    url: str
    caption: str | None = None
    attribution: str | None = None


class UnitOutputSchema(BaseModel):
    """Facility output schema"""

    code: str
    dispatch_type: DispatchType
    fueltech_id: str
    status_id: str
    capacity_registered: float | None = None
    capacity_maximum: float | None = None
    storage_capacity: float | None = None
    emissions_factor_co2: float | None = None
    expected_closure_date: date | None = None
    commencement_date: date | None = None
    closure_date: date | None = None


class FacilityOutputSchema(BaseModel):
    """Station output schema"""

    code: str
    name: str
    network_id: str
    network_region: str
    website: str | None = None
    description: str | None = None
    wikipedia: str | None = None
    photos: list[FacilityPhotoOutputSchema] | None = None
    location: dict[str, float | str] | None = None
    units: list[UnitOutputSchema] | None = None

    # Sanity fields
    updated_at: datetime | None = None
