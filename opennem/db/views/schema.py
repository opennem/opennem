"""


"""

from opennem.schema.core import BaseConfig

from .utils import format_offset


class ContinuousAggregationPolicy(BaseConfig):
    """Defines a continuous aggregation policy as used by
    timescale db. The map will destroy/create these"""

    interval: str
    start_interval: str | None
    end_interval: str | None

    @property
    def schedule_interval(self) -> str:
        return format_offset(self.interval)

    @property
    def start_offset(self) -> str:
        if self.start_interval:
            return format_offset(self.start_interval)

        return "NULL"

    @property
    def end_offset(self) -> str:
        if self.end_interval:
            return format_offset(self.end_interval)

        return "NULL"


class ViewDefinition(BaseConfig):
    """Defines a view (very useful docstrings!)"""

    # Priority determines order views
    # are processed in. probably better
    # done with a depends_on but eyyyy
    priority: int = 0

    name: str

    materialized: bool = False

    filepath: str

    view_content: str | None

    # Creates a unique index
    primary_key: list[str] | None

    # Create other indexes
    indexes: list[str] | None

    aggregation_policy: ContinuousAggregationPolicy | None
