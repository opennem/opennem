""" Reads the project version

@NOTE updated to dynamically update with build scripts
"""
import logging

from opennem import __version__

logger = logging.getLogger(__name__)

version = __version__

release = version


def get_version() -> str:
    """@TODO remove this and use poetry versioning"""

    return version
