"""
Notebook init file
"""

import logging
import sys
import warnings
from pathlib import Path

on_path = str(Path(__file__).parent.parent)

if on_path not in sys.path:
    sys.path.append(on_path)


from opennem.settings import settings  # noqa

logger = logging.getLogger("opennem.notebook")

__all__ = ["settings", "logging", "logger"]

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
