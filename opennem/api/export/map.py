"""
    Generates the map of queries and paths to export to S3 buckets
    for opennem.org.au

"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel

from opennem.api.stats.controllers import ScadaDateRange, get_scada_range_optimized
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.network_region_bom_station_map import get_network_region_weather_station
from opennem.core.networks import NetworkAPVI, NetworkAU, NetworkNEM, NetworkSchema, NetworkWEM
from opennem.schema.network import NetworkAEMORooftop, NetworkAEMORooftopBackfill, NetworkOpenNEMRooftopBackfill
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.version import get_version, get_version_model

logger = logging.getLogger(__name__)

STATS_FOLDER = "stats"
MAJOR_VERSION = get_version_model().major


class StatType(Enum):
    power = "power"
    energy = "energy"
    interchange = "interchange"
    marketvalue = "market_value"
    emissions = "emissions"
    gov = "gov"


class PriorityType(Enum):
    live = 1
    daily = 2
    monthly = 3
    history = 4


def date_range_from_week(year: int, week: int, network: NetworkSchema | None = None) -> ScadaDateRange:
    """
    Get a scada date range from week number with
    network awareness
    """
    start_date_str = f"{year}-W{week - 1}-1"
    start_date_dt = datetime.strptime(start_date_str, "%Y-W%W-%w")

    end_date = start_date_dt + timedelta(days=7)

    scada_range = ScadaDateRange(start=start_date_dt, end=end_date, network=network)

    return scada_range


def priority_from_name(priority_name: str) -> PriorityType:
    """Get the PriorityType enum def from a priority string name"""
    priority_names = [i.name for i in PriorityType]

    if priority_name not in priority_names:
        raise Exception(f"Could not find priority: {priority_name}")

    return PriorityType[priority_name]


class StatExport(BaseModel):
    """Defines an export map - a set of variables that produces a JSON export"""

    stat_type: StatType = StatType.energy
    priority: PriorityType = PriorityType.live
    country: str
    network: NetworkSchema
    networks: list[NetworkSchema] | None = None
    network_region: str | None = None
    network_region_query: str | None = None
    date_range: ScadaDateRange | None = None
    bom_station: str | None = None
    year: int | None = None
    week: int | None = None
    period: TimePeriod | None = None
    interval: TimeInterval
    file_path: str | None = None

    @property
    def path(self) -> str:
        _path_components = [
            f"v{MAJOR_VERSION}",
            STATS_FOLDER,
            self.country,
            self.network.code,
        ]

        if self.network_region:
            _path_components.append(self.network_region)

        _path_components.append(self.stat_type.value)

        # only show the period when it's not explicitly a year
        if self.period and not self.year:
            _path_components.append(self.period.period_human)

        if self.week:
            _path_components.append("week")

        if self.year:
            _path_components.append(str(self.year))

        if self.week:
            _path_components.append(str(self.week))

        dir_path = "/".join([str(i) for i in _path_components])

        return f"{dir_path}.json"


class StatMetadata(BaseModel):
    """Defines a set of export maps with methods to filter"""

    date_created: datetime
    version: str | None
    resources: list[StatExport]

    def get_by_stat_type(self, stat_type: StatType) -> StatMetadata:
        em = self.copy()
        em.resources = list(filter(lambda s: s.stat_type == stat_type, self.resources))
        return em

    def get_by_network_id(
        self,
        network_id: str,
    ) -> StatMetadata:
        em = self.copy()
        em.resources = list(filter(lambda s: s.network.code == network_id, self.resources))
        return em

    def get_by_network_region(
        self,
        network_region: str,
    ) -> StatMetadata:
        em = self.copy()
        em.resources = list(filter(lambda s: s.network_region == network_region, self.resources))
        return em

    def get_by_year(
        self,
        year: int,
    ) -> StatMetadata:
        em = self.copy()
        em.resources = list(filter(lambda s: s.year == year, self.resources))
        return em

    def get_by_years(
        self,
        years: list[int],
    ) -> StatMetadata:
        em = self.copy()
        em.resources = list(filter(lambda s: s.year in years, self.resources))
        return em

    def get_by_priority(self, priority: PriorityType) -> StatMetadata:
        em = self.copy()
        em.resources = list(
            filter(
                lambda s: s.priority == priority,
                self.resources,
            )
        )
        return em


def generate_export_map() -> StatMetadata:
    """
    Generates a map of all export JSONs

    """
    networks = [NetworkNEM, NetworkWEM]

    if not networks:
        raise Exception("No networks")

    country = "au"

    _exmap = []

    # @TODO derive this
    scada_range = get_scada_range_optimized(network=NetworkAU)

    if not scada_range:
        raise Exception("Require a scada range for NetworkAU")

    power_periods = [human_to_period("7d"), human_to_period("30d")]

    for power_period in power_periods:
        export = StatExport(
            stat_type=StatType.power,
            priority=PriorityType.live,
            country=country,
            date_range=scada_range,
            network=NetworkAU,
            networks=[
                NetworkNEM,
                NetworkWEM,
                NetworkAEMORooftop,
                NetworkOpenNEMRooftopBackfill,
                NetworkAPVI,
            ],
            interval=NetworkAU.get_interval(),
            period=power_period,
        )

        _exmap.append(export)

    for year in range(
        datetime.now().year,
        scada_range.start.year - 1,
        -1,
    ):
        export = StatExport(
            stat_type=StatType.energy,
            priority=PriorityType.daily,
            country=country,
            date_range=scada_range,
            network=NetworkAU,
            networks=[
                NetworkNEM,
                NetworkWEM,
                NetworkAEMORooftop,
                NetworkAEMORooftopBackfill,
                NetworkAPVI,
            ],
            year=year,
            interval=human_to_interval("1d"),
            period=human_to_period("1Y"),
        )
        _exmap.append(export)

    export = StatExport(
        stat_type=StatType.energy,
        priority=PriorityType.monthly,
        country=country,
        date_range=scada_range,
        network=NetworkAU,
        networks=[
            NetworkNEM,
            NetworkWEM,
            NetworkAEMORooftop,
            NetworkAEMORooftopBackfill,
            NetworkAPVI,
        ],
        interval=human_to_interval("1M"),
        period=human_to_period("all"),
    )
    _exmap.append(export)

    # for each network
    for network_schema in networks:
        scada_range = get_scada_range_optimized(network=network_schema)
        bom_station = get_network_region_weather_station(network_schema.code)

        for power_period in power_periods:
            export = StatExport(
                stat_type=StatType.power,
                priority=PriorityType.live,
                country=network_schema.country,
                date_range=scada_range,
                network=network_schema,
                bom_station=bom_station,
                interval=network_schema.get_interval(),
                period=power_period,
            )

            if network_schema.code == "WEM":
                export.networks = [NetworkWEM, NetworkAPVI]
                export.network_region_query = "WEM"

            if network_schema.code == "NEM":
                export.networks = [NetworkNEM, NetworkAEMORooftop, NetworkOpenNEMRooftopBackfill]

            _exmap.append(export)

        if not scada_range:
            raise Exception(f"Require a scada range for network: {network_schema.code}")

        for year in range(
            datetime.now().year,
            scada_range.start.year - 1,
            -1,
        ):
            export = StatExport(
                stat_type=StatType.energy,
                priority=PriorityType.daily,
                country=network_schema.country,
                date_range=scada_range,
                network=network_schema,
                bom_station=bom_station,
                year=year,
                period=human_to_period("1Y"),
                interval=human_to_interval("1d"),
            )

            if network_schema.code == "WEM":
                export.networks = [NetworkWEM, NetworkAPVI]
                export.network_region_query = "WEM"

            if network_schema.code == "NEM":
                export.networks = [NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill]

            _exmap.append(export)

        export = StatExport(
            stat_type=StatType.energy,
            priority=PriorityType.monthly,
            country=network_schema.country,
            date_range=scada_range,
            network=network_schema,
            bom_station=bom_station,
            interval=human_to_interval("1M"),
            period=human_to_period("all"),
        )

        if network_schema.code == "WEM":
            export.networks = [NetworkWEM, NetworkAPVI]
            export.network_region_query = "WEM"

        if network_schema.code == "NEM":
            export.networks = [NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill]

        _exmap.append(export)

        # Skip cases like wem/wem where region is supurfelous
        if network_schema.code == "WEM":
            continue

        if not network_schema.regions:
            continue

        for region in network_schema.regions:
            # scada_range = get_scada_range_optimized(network=network_schema, network_region=region.code)
            bom_station = get_network_region_weather_station(region)

            if not scada_range:
                logger.error(f"Require a scada range for network {network_schema.code} and region {region}")
                continue

            for power_period in power_periods:
                export = StatExport(
                    stat_type=StatType.power,
                    priority=PriorityType.live,
                    country=network_schema.country,
                    date_range=scada_range,
                    network=network_schema,
                    network_region=region,
                    bom_station=bom_station,
                    period=power_period,
                    interval=network_schema.get_interval(),
                )

                if network_schema.code == "WEM":
                    export.networks = [NetworkWEM, NetworkAPVI]
                    export.network_region_query = "WEM"

                if network_schema.code == "NEM":
                    export.networks = [NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill]

                _exmap.append(export)

            for year in range(
                datetime.now().year,
                scada_range.start.year - 1,
                -1,
            ):
                export = StatExport(
                    stat_type=StatType.energy,
                    priority=PriorityType.daily,
                    country=network_schema.country,
                    date_range=scada_range,
                    network=network_schema,
                    network_region=region,
                    networks=[NetworkNEM, NetworkAEMORooftop, NetworkOpenNEMRooftopBackfill],
                    bom_station=bom_station,
                    year=year,
                    period=human_to_period("1Y"),
                    interval=human_to_interval("1d"),
                )
                _exmap.append(export)

            export = StatExport(
                stat_type=StatType.energy,
                priority=PriorityType.monthly,
                country=network_schema.country,
                date_range=scada_range,
                network=network_schema,
                networks=[NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill],
                network_region=region,
                bom_station=bom_station,
                period=human_to_period("all"),
                interval=human_to_interval("1M"),
            )

            if network_schema.code == "WEM":
                export.networks = [NetworkWEM, NetworkAPVI]
                export.network_region_query = "WEM"

            if network_schema.code == "NEM":
                export.networks = [NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill]

            _exmap.append(export)

    export_meta = StatMetadata(date_created=datetime.now(), version=get_version(), resources=_exmap)

    return export_meta


def get_export_map() -> StatMetadata:
    return generate_export_map()


if __name__ == "__main__":
    pass
