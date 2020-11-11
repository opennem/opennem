"""
    Generates the map of queries and paths to export to S3 buckets
    for opennem.org.au

"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from opennem.api.stats.controllers import ScadaDateRange, get_scada_range
from opennem.api.time import human_to_period
from opennem.core.network_region_bom_station_map import (
    get_network_region_weather_station,
)
from opennem.core.networks import (
    NetworkAU,
    NetworkNEM,
    NetworkSchema,
    NetworkWEM,
    network_from_network_code,
)
from opennem.db import SessionLocal
from opennem.db.models.opennem import Network
from opennem.schema.time import TimePeriod
from opennem.utils.version import VersionPart, get_version

VERSION_MAJOR = get_version(version_part=VersionPart.MAJOR)
STATS_FOLDER = "stats"


class StatType(Enum):
    power = "power"
    energy = "energy"


class PriorityType(Enum):
    live = 1
    daily = 2
    monthly = 3


class StatExport(BaseModel):
    stat_type: StatType = StatType.energy
    priority: PriorityType = PriorityType.live
    country: str
    network: NetworkSchema
    networks: Optional[List[NetworkSchema]]
    network_region: Optional[str]
    date_range: ScadaDateRange
    bom_station: Optional[str]
    year: Optional[int]
    period: Optional[TimePeriod]
    file_path: Optional[str]

    @property
    def path(self):
        _path_components = [
            f"v{VERSION_MAJOR}",
            STATS_FOLDER,
            self.country,
            self.network.code,
        ]

        if self.network_region:
            _path_components.append(self.network_region)

        _path_components.append(self.stat_type.value)

        if self.period:
            _path_components.append(self.period.period_human)

        if self.year:
            _path_components.append(self.year)

        dir_path = "/".join([str(i) for i in _path_components])

        return "{}.json".format(dir_path)


class StatMetadata(BaseModel):
    date_created: datetime
    version: Optional[str]
    resources: List[StatExport]

    def get_by_stat_type(
        self, stat_type: StatType, priority: Optional[PriorityType] = None
    ) -> List[StatExport]:
        if priority:
            return list(
                filter(
                    lambda s: s.stat_type == stat_type
                    and s.priority == priority,
                    self.resources,
                )
            )

        return list(filter(lambda s: s.stat_type == stat_type, self.resources))


EXPORT_MAP = []


def get_export_map() -> StatMetadata:
    """
        Generates a map of all export JSONs

    """
    session = SessionLocal()

    networks = session.query(Network).all()

    if not networks:
        raise Exception("No networks")

    countries = list(set([network.country for network in networks]))

    _exmap = []

    for country in countries:
        # @TODO derive this
        scada_range = get_scada_range(
            network=NetworkAU, networks=[NetworkNEM, NetworkWEM]
        )

        export = StatExport(
            stat_type=StatType.power,
            priority=PriorityType.live,
            country=country,
            date_range=scada_range,
            network=NetworkAU,
            networks=[NetworkNEM, NetworkWEM],
            period=human_to_period("7d"),
        )

        _exmap.append(export)

        for year in range(
            datetime.now().year, scada_range.start.year - 1, -1,
        ):
            export = StatExport(
                stat_type=StatType.energy,
                priority=PriorityType.daily,
                country=country,
                date_range=scada_range,
                network=NetworkAU,
                networks=[NetworkNEM, NetworkWEM],
                year=year,
            )
            _exmap.append(export)

        export = StatExport(
            stat_type=StatType.energy,
            priority=PriorityType.monthly,
            country=country,
            date_range=scada_range,
            network=NetworkAU,
            networks=[NetworkNEM, NetworkWEM],
            period=human_to_period("all"),
        )
        _exmap.append(export)

    for network in networks:
        network_schema = network_from_network_code(network.code)
        scada_range = get_scada_range(network=network_schema)
        bom_station = get_network_region_weather_station(network.code)

        export = StatExport(
            stat_type=StatType.power,
            priority=PriorityType.live,
            country=network.country,
            date_range=scada_range,
            network=network_schema,
            bom_station=bom_station,
            period=human_to_period("7d"),
        )
        _exmap.append(export)

        for year in range(
            datetime.now().year, scada_range.start.year - 1, -1,
        ):
            export = StatExport(
                stat_type=StatType.energy,
                priority=PriorityType.daily,
                country=network.country,
                date_range=scada_range,
                network=network_schema,
                bom_station=bom_station,
                year=year,
            )
            _exmap.append(export)

        export = StatExport(
            stat_type=StatType.energy,
            priority=PriorityType.monthly,
            country=network.country,
            date_range=scada_range,
            network=network_schema,
            bom_station=bom_station,
            period=human_to_period("all"),
        )
        _exmap.append(export)

        # Skip cases like wem/wem where region is supurfelous
        if len(network.regions) < 2:
            continue

        for region in network.regions:
            scada_range = get_scada_range(
                network=network_schema, network_region=region
            )
            bom_station = get_network_region_weather_station(region)

            export = StatExport(
                stat_type=StatType.power,
                priority=PriorityType.live,
                country=network.country,
                date_range=scada_range,
                network=network_schema,
                network_region=region.code,
                bom_station=bom_station,
                period=human_to_period("7d"),
            )

            _exmap.append(export)

            for year in range(
                datetime.now().year, scada_range.start.year - 1, -1,
            ):
                export = StatExport(
                    stat_type=StatType.energy,
                    priority=PriorityType.daily,
                    country=network.country,
                    date_range=scada_range,
                    network=network_schema,
                    network_region=region.code,
                    bom_station=bom_station,
                    year=year,
                )
                _exmap.append(export)

            export = StatExport(
                stat_type=StatType.energy,
                priority=PriorityType.monthly,
                country=network.country,
                date_range=scada_range,
                network=network_schema,
                network_region=region.code,
                bom_station=bom_station,
                period=human_to_period("all"),
            )
            _exmap.append(export)

    export_meta = StatMetadata(
        date_created=datetime.now(), version=get_version(), resources=_exmap
    )

    return export_meta


if __name__ == "__main__":
    map = get_export_map()
    map_json = [i.json(exclude_unset=True, indent=4) for i in map]

    for i in map:
        print(i.path)

    # print(map_json)
