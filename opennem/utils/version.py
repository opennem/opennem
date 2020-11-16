from enum import Enum
from pathlib import Path
from typing import Optional

import tomlkit
from packaging.version import LegacyVersion, parse


def _get_project_meta():
    pyproject = Path(__file__).parent / "../../pyproject.toml"

    if not pyproject.is_file():
        return None

    with pyproject.open() as pp_file:
        file_contents = pp_file.read()

    return tomlkit.parse(file_contents)["tool"]["poetry"]


pkg_meta = _get_project_meta()
version = None

if pkg_meta:
    project = str(pkg_meta["name"])
    copyright = "2020, OpenNEM"
    version = str(pkg_meta["version"])

release = version


class VersionPart(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


def get_version(version_part: Optional[VersionPart] = None) -> str:
    if not version:
        return ""

    version_parsed = parse(version)

    if not version_part:
        return version

    if isinstance(version_parsed, LegacyVersion):
        return version

    if version_part == VersionPart.MAJOR:
        return str(version_parsed.major)

    if version_part == VersionPart.MINOR:
        return str(version_parsed.minor)

    if version_part == VersionPart.PATCH:
        return str(version_parsed.minor)

    return version
