"""
Notebook init file
"""

import logging
import sys
import warnings
from pathlib import Path

from opennem.settings import settings

logger = logging.getLogger("opennem.notebook")

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

on_path = str(Path.cwd().parent)

if on_path not in sys.path:
    sys.path.append(on_path)
