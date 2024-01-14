from datetime import datetime

from pydantic import BaseModel


class SchemaFacilityScada(BaseModel):
    network_id: str
    trading_interval: datetime
    facility_code: str
    generated: float = 0.0
    eoi_quantity: float | None = None
    is_forecast: bool = False
    energy_quality_flag: int = 0


class SchemaBalancingSummary(BaseModel):
    trading_interval: datetime
    network_id: str
    network_region: str
    price: float | None
    price_dispatch: float | None
    is_forecast: bool = False
