
from datetime import datetime
from typing import Optional

from .core import BaseConfig


class BomStationSchema(BaseConfig):
    code: str
    state: str
    name: str
    web_code: Optional[str]
    name_alias: Optional[str]
    registered: datetime

    priority: int
    is_capital: bool = False

    website_url: Optional[str]
    feed_url: Optional[str]
