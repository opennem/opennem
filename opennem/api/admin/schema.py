from datetime import datetime

from opennem.api.schema import ApiBase
from opennem.core.networks import NetworkSchema


class ScraperStats(ApiBase):
    scada_intervals: int
    scada_min: datetime
    scada_max: datetime


class ScraperStatsResult(ApiBase):
    network: NetworkSchema
    stats: ScraperStats
