""" Reads the project version

@NOTE updated to dynamically update with build scripts
"""
import semantic_version

from opennem import __version__ as version


def get_version() -> str:
    """@TODO remove this and use poetry versioning"""
    return version


def get_version_components() -> semantic_version.Version:
    """Gets the version components"""
    return semantic_version.Version(version)
