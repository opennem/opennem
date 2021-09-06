"""Module with project meta details and paths. Used in the core import
module, in settings and in loading resources"""

import importlib.resources as impres
from importlib.metadata import PackageNotFoundError, version


def get_version_from_importlib() -> str:
    try:
        _version = version("package-name")
    except PackageNotFoundError:
        # package is not installed
        pass

    return _version


def get_module_path() -> str:
    """Returns the core module path. In frozen packages this gives us the temp
    directory"""
    with impres.path("opennem", "__init__.py") as ph:
        _path = str(ph)
        return _path
