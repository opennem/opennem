from datetime import datetime

from .core import BaseConfig


class BomStationSchema(BaseConfig):
    code: str
    state: str
    name: str
    web_code: str | None = None
    name_alias: str | None = None
    registered: datetime | None = None

    priority: int
    is_capital: bool = False

    website_url: str | None = None
    feed_url: str | None = None
