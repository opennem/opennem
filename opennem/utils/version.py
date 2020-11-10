from enum import Enum
from typing import Optional, Union

from packaging.version import Version, parse
from pkg_resources import get_distribution

try:
    VERSION = get_distribution("opennem").version
except Exception:
    VERSION = None

__version__ = VERSION


class VersionPart(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


def get_version(
    version_part: Optional[VersionPart] = None, as_string: bool = True
) -> Union[str, Version]:
    version_parsed = parse(VERSION)

    if not version_part:
        if as_string:
            return VERSION
        return version_parsed

    if version_part == VersionPart.MAJOR:
        return version_parsed.major

    if version_part == VersionPart.MINOR:
        return version_parsed.minor

    if version_part == VersionPart.PATCH:
        return version_parsed.minor

