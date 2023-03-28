from datetime import datetime
from decimal import Decimal

from opennem.schema.core import BaseConfig


class ExportResultRow(BaseConfig):
    interval: datetime
    result: float | int | None | Decimal = None
    group_by: str | None = None


class ControllerReturn(BaseConfig):
    last_modified: datetime | None = None
    server_latest: datetime | None = None
    total_records: int = 0
    inserted_records: int = 0
    processed_records: int = 0
    errors: int = 0
    error_detail: list[str | None] = []
