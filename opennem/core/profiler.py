""" OpenNEM module for tasks and their analytics

This will track the tasks that are run and their status and output
as well as the time taken to run them.

Optionally log to the database or another data persistance option
"""

import enum
import functools
import inspect
import logging
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from types import FrameType
from typing import Any, cast
from zoneinfo import ZoneInfo

from sqlalchemy import event as sa_event
from sqlalchemy import text as sql_text
from sqlalchemy.engine import Engine

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db import get_database_engine
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.network import NetworkSchema

# from opennem.utils.timedelta import timedelta_to_string

logger = logging.getLogger("opennem.profiler")


# levels of profiler, and methods and the global used down in the decorator
class ProfilerLevel(enum.Enum):
    """Profiler levels"""

    NOISY = 0
    DEBUG = 1
    INFO = 2
    ESSENTIAL = 3


class ProfilerRetentionTime(enum.Enum):
    """How long to retain profiler record for"""

    FOREVER = "forever"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"


def profiler_level_string_to_enum(level: str) -> ProfilerLevel:
    """Converts a string to a profiler level"""
    if level.upper() == "NOISY":
        return ProfilerLevel.NOISY

    if level.upper == "INFO":
        return ProfilerLevel.INFO

    if level.upper == "ESSENTIAL":
        return ProfilerLevel.ESSENTIAL

    raise Exception("Invalid profiler level")


PROFILE_LEVEL = profiler_level_string_to_enum(settings.profiler_level)


# method used to discover the invokee
def profile_retrieve_caller_name() -> str:
    """Return the calling function's name.

    @NOTE need to step up twice since it's a decorator. Don't use this on
    other generic methods
    """
    # Ref: https://stackoverflow.com/a/57712700/
    return cast(FrameType, cast(FrameType, inspect.currentframe()).f_back.f_back).f_code.co_name


def get_id_profile_url(id: uuid.UUID) -> str:
    """Link to internal tracing profile for a given id"""
    return f"https://tracing.internal.opennem.org.au/profile/{settings.env.lower()}/{id}"


def get_now() -> datetime:
    """Utility function to get now

    @NOTE add timezone
    """
    return datetime.now().astimezone(ZoneInfo("Australia/Sydney"))


def chop_delta_microseconds(delta: timedelta) -> timedelta:
    """Removes microsevonds from a timedelta"""
    return delta - timedelta(microseconds=delta.microseconds)


def bind_sqlalchemy_events() -> None:
    """Binds event listeners on sqlalchemy to log queries and times"""

    @sa_event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.time())
        logger.debug("Start Query: %s", statement)

    @sa_event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info["query_start_time"].pop(-1)
        logger.debug("Query Complete!")
        logger.debug("Total Time: %f", total)


def cleanup_database_task_profiles_basedon_retention() -> None:
    """This will clean up the database tasks based on their retention period"""
    engine = get_database_engine()

    query = """
        delete from task_profile where
            (retention_period = 'day' and now() - interval '1 day' < time_start) or
            (retention_period = 'week' and now() - interval '7 days' < time_start) or
            (retention_period = 'month' and now() - interval '30 days' < time_start)
    """

    with engine.connect() as conn:
        conn.execute(sql_text(query))


def parse_kwargs_value(value: Any) -> str:
    """Parses profiler argument objects. This should be done
    using dunder methods but pydantic has a bug with sub-classes"""
    if isinstance(value, NetworkSchema):
        return f"NetworkSchema({value.code})"

    if isinstance(value, NetworkRegion):
        return f"NetworkRegion({value.code})"

    if hasattr(value, "code"):
        return f"{value.code}"

    return str(value)


def format_args_into_string(args: tuple[str], kwargs: dict[str, str]) -> str:
    """This takes args and kwargs from the profiled method and formats
    them out into a string for logging."""
    args_string = ", ".join([f"'{i}'" for i in args]) if args else ""
    kwargs_string = ", ".join(f"{key}={parse_kwargs_value(value)}" for key, value in kwargs.items())

    # add a separator if both default and named args are present
    if args_string and kwargs_string:
        args_string += ", "

    return f"({args_string}{kwargs_string})"


def log_task_profile_to_database(
    task_name: str,
    time_start: datetime,
    time_end: datetime,
    invokee_name: str = "",
    level: ProfilerLevel | None = None,
    retention_period: ProfilerRetentionTime | None = None,
) -> uuid.UUID:
    """Log the task profile to the database"""

    engine = get_database_engine()
    id = uuid.uuid4()

    with engine.connect() as conn:
        conn.execute(
            sql_text(
                """
                    INSERT INTO task_profile (
                        id,
                        task_name,
                        time_start,
                        time_end,
                        errors,
                        retention_period,
                        level
                    ) VALUES (
                        :id,
                        :task_name,
                        :time_start,
                        :time_end,
                        :errors,
                        :retention_period,
                        :level
                    ) returning id
                    """
            ),
            id=id,
            task_name=task_name,
            time_start=time_start,
            time_end=time_end,
            errors=0,
            retention_period=retention_period.value if retention_period else "",
            level=level.name.lower() if level else "",
        )

    return id


def profile_task(
    send_slack: bool = False,
    persist_profile: bool = True,
    link_tracing: bool = False,
    include_args: bool = False,
    message_fmt: str | None = None,
    message_prepend: bool = True,
    level: ProfilerLevel = ProfilerLevel.NOISY,
    retention_period: ProfilerRetentionTime = ProfilerRetentionTime.FOREVER,
) -> Callable:
    """Profile a task and log the time taken to run it

    :param send_slack: Send a slack message with the profile
    :param persist_profile: Persist the profile to the database
    :param link_tracing: Add a link to the profile in the logs
    :param include_args: Include the arguments passed to the task in the logs
    :param message_fmt: A custom message format
    :param message_prepend: Prepend the message with the task name
    """

    def profile_task_decorator(task: Any, *args: Any, **kwargs: Any) -> Any:
        @functools.wraps(task)
        def _task_profile_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for the task"""
            logger.info(f"Running task: {task.__name__}")

            # get the method that invoked this method for logging purposes
            invokee_method_name: str = ""

            try:
                invokee_method_name = profile_retrieve_caller_name()
                logger.info(f"Invoked by: {invokee_method_name}")
            except Exception as e:
                logger.error(e)

            # time_start = time.perf_counter()
            dtime_start = get_now()

            run_task_output = task(*args, **kwargs)

            dtime_end = get_now()

            if level and level.value < PROFILE_LEVEL.value:
                logger.debug(f"Task {task.__name__} complete and returning since not level")
                return run_task_output

            # calculate wall clock time
            wall_clock_time = chop_delta_microseconds(dtime_end - dtime_start)

            wall_clock_human = f"{wall_clock_time.total_seconds()}s"

            id: uuid.UUID | None = None

            if persist_profile:
                id = log_task_profile_to_database(
                    task_name=task.__name__,
                    time_start=dtime_start,
                    time_end=dtime_end,
                    retention_period=retention_period,
                    level=level,
                )

            id_msg: str = ""

            if link_tracing:
                id_msg = f"({get_id_profile_url(id)})" if id else ""

            # argument string
            method_args_string: str = ""

            if include_args:
                method_args_string = format_args_into_string(args, kwargs)  # type: ignore

            # default message format
            profile_message = f"[{settings.env}]{id_msg} `{task.__name__}{method_args_string}` in " f"{wall_clock_human} "

            # custom message format
            if message_fmt:
                combined_arg_and_env_dict = {**locals(), **kwargs}

                logger.debug(combined_arg_and_env_dict)

                custom_message = ""

                try:
                    custom_message = message_fmt.format(**combined_arg_and_env_dict)
                except Exception as e:
                    logger.error(e)

                profile_message = (
                    f"[{settings.env}] " + custom_message
                    if not message_prepend
                    else "" + f" `{task.__name__}` " + custom_message
                    if message_prepend
                    else "" + f" in {wall_clock_human}"
                )

            if send_slack:
                slack_message(profile_message)

            logger.info(profile_message)

            return run_task_output

        return _task_profile_wrapper

    return profile_task_decorator


def run_outer_test_task() -> None:
    test_task(message="test inner")


@profile_task(send_slack=True, message_fmt="arg={message}=", message_prepend=True)
def test_task(message: str | None = None) -> None:
    """Test task"""
    # time.sleep(random.randint(1, ))
    print(f"complete: {message}")


if __name__ == "__main__":
    # test_task(message="test mess")
    run_outer_test_task()
