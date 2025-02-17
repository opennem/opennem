"""
OpenNEM main module entry

Setup main module entry point with sanity checks, settings init
and sentry.

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

import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from platform import platform

import logfire
from dotenv import load_dotenv
from rich.console import Console

from opennem.settings_schema import OpennemSettings
from opennem.utils.log_config import LOGGING_CONFIG
from opennem.utils.logging_setup import setup_root_logger
from opennem.utils.project_path import get_project_path
from opennem.utils.security import obfuscate_dsn_password
from opennem.utils.sentry import setup_sentry
from opennem.utils.settings import load_env_file

logger = logging.getLogger("opennem")

# Module variables

__version__ = "4.0.3.dev1"

# console
console = Console()

# Setup logging - root logger and handlers
setup_root_logger()

# module constants
PYTHON_VERSION = ".".join([str(i) for i in (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)])
SYSTEM_STRING = platform()
ENV = os.getenv("ENV", default="local")


console.print(f" * Loading OpenNEM ENV: [b magenta]{ENV}[/b magenta]")
console.print(
    f" * OpenNEM Version: [b magenta]{__version__}[/]. Python version: [b magenta]{PYTHON_VERSION}[/]."
    f" System: [b magenta]{SYSTEM_STRING}[/]"
)

env_files = load_env_file(ENV)

if not env_files:
    console.print(" * No env files found. Using system environment only.")

for _env_file in env_files:
    _env_full_path = Path(_env_file).resolve()
    console.print(f" * Loading env file: {_env_full_path}")
    load_dotenv(dotenv_path=_env_file, override=True)

settings: OpennemSettings = OpennemSettings()  # type: ignore

# Setup sentry
if settings.sentry_url:
    setup_sentry(sentry_url=settings.sentry_url, environment=ENV)
    console.print(f" * Sentry configured at [red bold encircle]{obfuscate_dsn_password(settings.sentry_url)}[/]")
else:
    console.print(" * Sentry not configured")


# setup logfire
if not settings.is_local:
    logfire.configure(
        service_name="opennem",
        service_version=__version__,
        environment=ENV,
        code_source=logfire.CodeSource(repository="https://github.com/opennem/opennem", revision="master"),
    )

if settings.db_url:
    console.print(f" * Using database connection: [red bold encircle]{obfuscate_dsn_password(settings.db_url)}[/]")

if settings.redis_url:
    console.print(f" * Using redis connection: [red bold encircle]{obfuscate_dsn_password(str(settings.redis_url))}[/]")

if settings.clickhouse_url:
    console.print(f" * Using clickhouse connection: [red bold encircle]{obfuscate_dsn_password(str(settings.clickhouse_url))}[/]")

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

PROJECT_PATH = get_project_path()


# import other modules now that init has completed
from opennem.core.feature_flags import get_list_of_enabled_features  # noqa: E402

# Log current timezone to console
console.print(f" * Current timezone: {datetime.now().astimezone().tzinfo} (settings: {settings.timezone})")
console.print(f" * Running from {PROJECT_PATH}")
console.print(f" * Enabled feature flags: {', '.join(get_list_of_enabled_features())}")
