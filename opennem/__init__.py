"""
OpenNEM main module entry

Setup main module entry point with sanity checks, settings init
and sentry.
"""
import logging
import logging.config
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from platform import platform

from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic.error_wrappers import _display_error_loc, _display_error_type_and_ctx
from rich.console import Console
from rich.prompt import Prompt

from opennem.settings_schema import OpennemSettings
from opennem.utils.log_config import LOGGING_CONFIG
from opennem.utils.security import obfuscate_dsn_password
from opennem.utils.sentry import setup_sentry
from opennem.utils.settings import load_env_file

logger = logging.getLogger("opennem")
warnings.filterwarnings("ignore", module="openpyxl")

# Module variables
__version__ = "3.13.2-alpha.5"
__env__ = "prod"
__package__ = "opennem"

# Check minimum required Python version
if sys.version_info < (3, 10):
    print(" * OpenNEM %s requires Python 3.10 or greater")
    sys.exit(1)

# console
console = Console()

# Setup logging - root logger and handlers
__root_logger = logging.getLogger()
__root_logger.setLevel(logging.INFO)
__root_logger_formatter = logging.Formatter(fmt=" * %(message)s")
num_handlers = len(__root_logger.handlers)

if num_handlers == 0:
    __root_logger.addHandler(logging.StreamHandler())

__root_logger.handlers[0].setFormatter(__root_logger_formatter)

# module constants
PYTHON_VERSION = ".".join([str(i) for i in (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)])
SYSTEM_STRING = platform()
ENV = os.getenv("ENV", default="local")
VERSION = __version__

console.print(f" * Loading OpenNEM ENV: [b magenta]{ENV}[/b magenta]")
console.print(
    f" * OpenNEM Version: [b magenta]{VERSION}[/]. Python version: [b magenta]{PYTHON_VERSION}[/]."
    f" System: [b magenta]{SYSTEM_STRING}[/]"
)

env_files = load_env_file(ENV)

# Load the env files
# @TODO add logging
"""
Settings files - read settings from env

Process:

 * Loads dotenv to read environment from .env files
 * Setup logging - root logger, read logging config, etc.
 * Settings init - read all env and init settings module

Will load environment in order:

 * `.env`
 * `.env.{environment}`
 * system env
 * pydantic settings

Environments:
  * local (default)
  * development
  * staging
  * production

"""
for _env_file in env_files:
    _env_full_path = Path(_env_file).resolve()
    console.print(f" * Loading env file: {_env_full_path}")
    load_dotenv(dotenv_path=_env_file, override=True)

# setup settings
# @NOTE don't use pydantics env file support since it doesn't support multiple
try:
    settings: OpennemSettings = OpennemSettings()
except ValidationError as e:
    logging.error(f"{len(e.errors())} validation errors in settings schema")

    for err_no, _validation_error in enumerate(e.errors()):
        logging.error(
            f'{_display_error_loc(_validation_error)}: {_validation_error["msg"]} \
                ({_display_error_type_and_ctx(_validation_error)})'
        )

    logging.info("Exiting")
    sys.exit(-1)


if settings.dry_run:
    console.print(" * Dry run (no database actions)")
else:
    console.print(f" * Using database connection: [red bold encircle]{obfuscate_dsn_password(settings.db_url)}[/]")

# skip if logging not configed
if LOGGING_CONFIG:
    logging.config.dictConfig(LOGGING_CONFIG)

    log_level = logging.getLevelName(settings.log_level)

    # set root log level
    logging.root.setLevel(log_level)

    opennem_logger = logging.getLogger("opennem")
    opennem_logger.setLevel(log_level)

    # other misc loggers
    logging.getLogger("PIL").setLevel(logging.ERROR)

IS_DEV = not settings.is_prod

# Setup sentry
if settings.sentry_url:
    setup_sentry(sentry_url=settings.sentry_url, environment=settings.env)


if __package__ not in sys.modules:
    raise Exception(f"Could not find {__package__} module")

if sys.modules[__package__].__file__:
    MODULE_DIR_PATH = Path(sys.modules[__package__].__file__).parent  # type: ignore
else:
    MODULE_DIR_PATH = Path(__file__).parent

DATA_DIR_PATH = MODULE_DIR_PATH / "data"
PROJECT_PATH = MODULE_DIR_PATH.parent


# Log current timezone to console
console.print(f" * Current timezone: {datetime.now().astimezone().tzinfo} (settings: {settings.timezone})")
console.print(f" * Running from {PROJECT_PATH}")

# Prod safety feature
if settings.is_prod and not os.environ.get("OPENNEM_CONFIRM_PROD", False):
    if Prompt.ask(" [bold red]* ⛔️ Running in PRODUCTION mode ⛔️ Continue? [/]", default="n", choices=["y", "n"]) == "n":
        console.print(" * [red]Exiting[/]")
        sys.exit(-1)
