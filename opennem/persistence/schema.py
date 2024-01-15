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
    network_id: str
    trading_interval: datetime
    forecast_load: float | None = None
    generation_scheduled: float | None = None
    generation_non_scheduled: float | None = None
    generation_total: float | None = None
    price: float | None
    network_region: str
    is_forecast: bool = False
    net_interchange: float | None = None
    demand_total: float | None = None
    price_dispatch: float | None
    net_interchange_trading: float | None
    demand: float | None = None
