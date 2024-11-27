from datetime import datetime

from pydantic import BaseModel


class FacilityScadaSchema(BaseModel):
    interval: datetime
    network_id: str
    facility_code: str
    generated: float = 0.0
    energy: float | None = None
    is_forecast: bool = False
    energy_quality_flag: int = 0


class BalancingSummarySchema(BaseModel):
    interval: datetime
    network_id: str
    forecast_load: float | None = None
    generation_scheduled: float | None = None
    generation_non_scheduled: float | None = None
    generation_total: float | None = None
    price: float | None = None
    network_region: str
    is_forecast: bool = False
    net_interchange: float | None = None
    demand_total: float | None = None
    price_dispatch: float | None = None
    net_interchange_trading: float | None = None
    demand: float | None = None
