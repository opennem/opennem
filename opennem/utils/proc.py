import os
import sys
from pathlib import Path


def running_as_scrapy() -> bool:
    """
    Detect if we're running as scrapy
    """

    # running in scrapyd
    if "SCRAPYD" in os.environ:
        return True

    # running as lib
    if not sys.argv or len(sys.argv) < 1:
        return False

    _cl = sys.argv[0]

    if Path(_cl).name in ["scrapy"]:
        return True

    return False
