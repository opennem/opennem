""" Utilities for exporters """

from opennem.controllers.output.schema import StatType
from opennem.schema.network import NetworkSchema
from opennem.utils.version import get_version_model

VERSION_MAJOR = get_version_model().major
STATS_FOLDER = "stats"


def get_export_output_path(
    network: NetworkSchema,
    stat_type: StatType,
    network_region: str | None = None,
    period=None,
    year: int | None = None,
    week_number: int | None = None,
) -> str:
    """Takes the attributes of an export and returns the path they should be saved to"""
    _path_components = [
        f"v{VERSION_MAJOR}",
        STATS_FOLDER,
        network.country,
        network.code,
    ]

    if network_region:
        _path_components.append(network_region)

    _path_components.append(stat_type.value)

    # only show the period when it's not explicitly a year
    if period and not year:
        _path_components.append(period.period_human)

    if week_number:
        _path_components.append("week")

    if year:
        _path_components.append(str(year))

    if week_number:
        _path_components.append(str(week_number))

    dir_path = "/".join([str(i) for i in _path_components])

    return f"{dir_path}.json"
