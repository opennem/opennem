"""Module with project meta details and paths. Used in the core import
module, in settings and in loading resources"""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def get_importlib_version() -> str:
    try:
        __version__ = version("package-name")
    except PackageNotFoundError:
        # package is not installed
        pass

    return __version__


def get_project_path() -> Path:
    pass
