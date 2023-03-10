from datetime import datetime

from .core import BaseConfig


class BomStationSchema(BaseConfig):
    code: str
    state: str
    name: str
    web_code: str | None
    name_alias: str | None
    registered: datetime | None

    priority: int
    is_capital: bool = False

    website_url: str | None
    feed_url: str | None
