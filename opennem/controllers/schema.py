from datetime import datetime

from opennem.schema.core import BaseConfig


class ControllerReturn(BaseConfig):
    last_modified: datetime | None = None
    server_latest: datetime | None = None
    total_records: int = 0
    inserted_records: int = 0
    processed_records: int = 0
    errors: int = 0
    error_detail: list[str | None] = []
