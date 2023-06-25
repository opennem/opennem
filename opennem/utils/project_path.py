""" Utilities for the project path """
import sys
from pathlib import Path


def get_project_path() -> Path:
    """Gets the project path from sys.modules"""
    return Path(sys.modules["opennem"].__file__).parent.parent
