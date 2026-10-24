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
    crawls_run: int | None = None
    # min/max interval of the rows written, so callers know which window a crawl touched (#764)
    interval_min: datetime | None = None
    interval_max: datetime | None = None

    def merge_interval_span(self, other: "ControllerReturn") -> None:
        """Widen this return's interval span to also cover another return's span."""
        if other.interval_min is not None and (self.interval_min is None or other.interval_min < self.interval_min):
            self.interval_min = other.interval_min

        if other.interval_max is not None and (self.interval_max is None or other.interval_max > self.interval_max):
            self.interval_max = other.interval_max
