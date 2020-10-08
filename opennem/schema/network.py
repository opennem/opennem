from pytz import timezone

from .core import BaseConfig


class NetworkSchema(BaseConfig):
    code: str
    country: str
    label: str
    timezone: str
    interval_size: int

    def get_timezone(self) -> timezone:
        return timezone(self.timezone)


NetworkNEM = NetworkSchema(
    code="NEM",
    label="NEM",
    country="au",
    timezone="Australia/Sydney",
    interval_size=5,
)
NetworkWEM = NetworkSchema(
    code="WEM",
    label="WEM",
    country="au",
    timezone="Australia/Perth",
    interval_size=30,
)


NETWORKS = [NetworkNEM, NetworkWEM]
