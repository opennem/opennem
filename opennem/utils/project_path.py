""" Utilities for the project path """
import sys
from pathlib import Path


def get_project_path() -> Path:
    """Gets the project path from sys.modules"""
    if __package__ not in sys.modules:
        raise Exception(f"Could not find {__package__} module")

    if sys.modules[__package__].__file__:
        return Path(sys.modules[__package__].__file__).parent.parent  # type: ignore

    return Path(__file__).parent
