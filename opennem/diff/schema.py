from typing import Optional

from pydantic import BaseModel


class StationSchema(BaseModel):
    name: str
    station_code: Optional[str] = None
    network_region: str
    status: str
    duid: str
    fueltech: Optional[str] = None
    capacity: Optional[float] = None

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
