from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from opennem.schema.core import BaseConfig


class ScadaInterval(object):
    date: datetime
    value: Optional[float]

    def __init__(self, date: datetime, value: Optional[float] = None):
        self.date = date
        self.value = value


class ScadaReading(Tuple[datetime, Optional[float]]):
    pass


class UnitScadaReading(BaseModel):
    code: str
    data: List[ScadaReading]


class StationScadaReading(BaseModel):
    code: str
    facilities: Dict[str, UnitScadaReading]


class OpennemDataHistory(BaseConfig):
    start: datetime
    last: datetime
    interval: str
    data: List[float]


class OpennemData(BaseConfig):
    region: str = ""
    network: str
    data_type: str
    units: str
    history: OpennemDataHistory

