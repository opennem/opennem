""" OpenNEM Startup Methods """

import sys
from platform import node, platform

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.utils.version import get_version

PYTHON_VERSION = ".".join([str(i) for i in (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)])
SYSTEM_STRING = platform()


def startup_banner_message() -> str:
    """This is a banner that is created on new deploy or startup"""
    return f"[{settings.env.lower()}] OpenNEM `v{get_version()}` worker started on host `{node()}`"


def worker_startup_alert() -> None:
    """This is fired when the worker starts"""
    slack_message(startup_banner_message())


def console_startup_banner() -> None:
    """The startup banner on the console and CLI"""
    print(f"Loading OpenNEM ENV {settings.env}")
    print(f"OpenNEM Version: {get_version()}. Python version: {PYTHON_VERSION}. System: {SYSTEM_STRING}")


# debug entry point
if __name__ == "__main__":
    print(startup_banner_message())
