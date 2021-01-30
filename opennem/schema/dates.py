from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, List, Optional, Tuple, Union

from pydantic import validator

from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeIntervalAPI, TimePeriodAPI
from opennem.settings import settings
from opennem.utils.interval import get_human_interval
from opennem.utils.timezone import get_current_timezone


class DateRange(BaseConfig):
    start: datetime
    end: datetime
    network: Optional[NetworkSchema]

    def _get_value_localized(self, field_name: str = "start") -> Any:
        timezone = get_current_timezone()
        date_aware = getattr(self, field_name)

        if self.network:
            timezone = self.network.get_timezone()

        date_aware = date_aware.astimezone(timezone)

        return date_aware

    def get_start_year(self) -> int:
        return self.start.year

    def get_start(self) -> datetime:
        return self._get_value_localized("start")

    def get_end(self) -> datetime:
        return self._get_value_localized("end")

    def get_start_sql(self, as_date: bool = False) -> str:
        return "'{}'".format(self.get_start() if not as_date else self.get_start().date())

    def get_end_sql(self, as_date: bool = False) -> str:
        return "'{}'".format(self.get_end() if not as_date else self.get_end().date())
