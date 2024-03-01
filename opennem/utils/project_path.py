"""Utilities for the project path"""

import sys
from pathlib import Path

MODULE_NAME = "opennem"


def get_project_path() -> Path:
    """Gets the project path from sys.modules"""
    if MODULE_NAME not in sys.modules:
        raise Exception("opennem module not loaded")

    module_file_path = sys.modules[MODULE_NAME].__file__

    if not module_file_path:
        raise Exception("opennem module not loaded")

    return Path(module_file_path).parent.parent
