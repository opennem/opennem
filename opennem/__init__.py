"""
OpenNEM main module entry

Setup main module entry point with sanity checks, settings init
and sentry.
"""
import sys
from os.path import realpath

# Check minimum required Python version
if sys.version_info < (3, 7):
    print("OpenNEM %s requires Python 3.7 or greater")
    sys.exit(1)


# Setup sentry
from opennem.settings import settings  # noqa: E402
from opennem.utils.sentry import setup_sentry  # noqa: E402

if settings.sentry_enabled:
    setup_sentry()


import logging  # noqa: E402

# Clean up default loggers so they're less noisy
# Kill warnings from various modules
import warnings  # noqa: E402

# Ignore noisy twisted deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="twisted")

# Core methods we reuire in loading the module
from opennem.utils.version import get_version  # noqa: E402


def get_module_path() -> None:
    _path = __import__("pkgutil").extend_path(__path__, __name__)

    # _path = list(set([realpath(i) for i in opennem.__path__])).pop()

    return _path


# Module variables
v = "3.7.0"
__env__ = "prod"
__version__ = get_version()
__path__ = __import__("pkgutil").extend_path(__path__, __name__)  # type: ignore
