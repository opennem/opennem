#!/usr/bin/env python
"""
Run tasks manuall from the command line
"""
import argparse
import logging
import sys

from opennem.api.export.map import priority_from_name
from opennem.api.export.tasks import export_all_daily, export_all_monthly, export_energy, export_metadata, export_power
from opennem.utils.version import get_version
from opennem.workers.scheduler import huey

logger = logging.getLogger("opennem.tasks")


def _setup_logger(verbosity: int) -> logging.Logger:
    logger.setLevel(logging.INFO)

    if verbosity >= 2:
        logger.setLevel(logging.DEBUG)
    elif verbosity >= 0:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)

    return logger


def flush_tasks() -> None:

    huey.flush()
    print("Flushed all tasks")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", nargs="?", default="power", help="Task type to run")
    parser.add_argument(
        "-p",
        "--priority",
        dest="priority",
        default="live",
        type=str,
        help="task priority type to run (default: live)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest="verbosity",
        default=0,
        help="verbose output (repeat for increased verbosity)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="run in debug mode",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=-1,
        default=0,
        dest="verbosity",
        help="quiet output (show errors only)",
    )
    parser.add_argument(
        "--latest",
        dest="latest",
        action="store_true",
        default=False,
        help="run only latest",
    )
    args = parser.parse_args()

    if args.debug:
        args.verbosity = 5

    _setup_logger(args.verbosity)

    print("opennem.tasks: v{}".format(get_version()))

    priority = priority_from_name(args.priority)

    if not priority:
        logger.error("Priority not found")
        return None

    print(args.task, priority)

    task_name = "export_{}".format(args.task)

    if task_name not in globals():
        logger.error("Task not found")
        return None

    _task = globals()[task_name]

    print("Running {} with priority {} and latest is {}".format(task_name, priority, args.latest))

    run = _task(priority=priority, latest=args.latest)

    return run


def cli() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as err:
        logger.error(str(err))
        logger.debug("", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
