"""
OpenNEM main module entry

Setup main module entry point with sanity checks, settings init
and sentry.
"""
import sys
from datetime import datetime
from pathlib import Path

# Setup console
from rich.console import Console  # noqa: E402
from rich.prompt import Prompt

console = Console()

# Check minimum required Python version
if sys.version_info < (3, 10):
    console.print(" * [red bold]OpenNEM %s requires Python 3.10 or greater[/]")
    sys.exit(1)


# Setup sentry
from opennem.settings import settings as opennem_settings  # noqa: E402
from opennem.utils.sentry import setup_sentry  # noqa: E402

if opennem_settings.sentry_enabled:
    setup_sentry()


import logging  # noqa: E402,F401

logger = logging.getLogger("opennem")

# Clean up default loggers so they're less noisy
# Kill warnings from various modules
import warnings  # noqa: E402

# Ignore noisy twisted deprecation warnings
warnings.filterwarnings("ignore", module="openpyxl")


# Module variables
__version__ = "3.13.0-beta.27"
__env__ = "prod"
__package__ = "opennem"


if __package__ not in sys.modules:
    raise Exception(f"Could not find {__package__} module")

if sys.modules[__package__].__file__:
    MODULE_DIR_PATH = Path(sys.modules[__package__].__file__).parent  # type: ignore
else:
    MODULE_DIR_PATH = Path(__file__).parent

DATA_DIR_PATH = MODULE_DIR_PATH / "data"
PROJECT_PATH = MODULE_DIR_PATH.parent


# Log current timezone to console
console.print(f" * Current timezone: {datetime.now().astimezone().tzinfo} (settings: {opennem_settings.timezone})")
console.print(f" * Running from {PROJECT_PATH}")

if opennem_settings.is_prod:
    if Prompt.ask(" [bold red]* ⛔️ Running in PRODUCTION mode ⛔️ Continue? [/]", default="n", choices=["y", "n"]) == "n":
        console.print(" * [red]Exiting[/]")
        sys.exit(-1)
