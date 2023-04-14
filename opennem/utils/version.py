""" Reads the project version

@NOTE updated to dynamically update with build scripts
"""
import semantic_version

version = "3.15.0-alpha.2"


def get_version() -> str:
    """@TODO remove this and use poetry versioning"""
    return version


def get_version_components() -> semantic_version.Version:
    """Gets the version components"""
    return semantic_version.Version(version)
