""" OpenNEM module for tasks and their analytics

This will track the tasks that are run and their status and output
as well as the time taken to run them.

Optionally log to the database or another data persistance option
"""

import functools
import logging
import random
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import event as sa_event
from sqlalchemy import text as sql_text
from sqlalchemy.engine import Engine

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db import get_database_engine
from opennem.schema.network import NetworkSchema
from opennem.utils.dates import chop_delta_microseconds
from opennem.utils.timedelta import timedelta_to_string

logger = logging.getLogger("opennem.profiler")


def get_id_profile_url(id: uuid.UUID) -> str:
    return f"https://trading.internal.opennem.org.au/profile/{settings.env.lower()}/{id}"


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


def parse_kwargs_value(value: Any) -> str:
    """Parses profiler argument objects. This should be done
    using dunder methods but pydantic has a bug with sub-classes"""
    if isinstance(value, NetworkSchema):
        return f"NetworkSchema({value.code})"
    return str(value)


def log_task_profile_to_database(task_name: str, time_start: datetime, time_end: datetime) -> uuid.UUID:
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
                        errors
                    ) VALUES (
                        :id,
                        :task_name,
                        :time_start,
                        :time_end,
                        :errors
                    ) returning id
                    """
            ),
            id=id,
            task_name=task_name,
            time_start=time_start,
            time_end=time_end,
            errors=0,
        )

    return id


def profile_task(
    send_slack: bool = False,
    persist_profile: bool = True,
    link_tracing: bool = False,
    include_args: bool = False,
) -> Callable:
    """Profile a task and log the time taken to run it"""

    def profile_task_decorator(task: Any, *args: Any, **kwargs: Any) -> Any:
        @functools.wraps(task)
        def _task_profile_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for the task"""
            logger.info(f"Running task: {task.__name__}")

            # time_start = time.perf_counter()
            dtime_start = datetime.now()

            run_task_output = task(*args, **kwargs)

            dtime_end = datetime.now()

            # calculate wall clock time
            wall_clock_time = chop_delta_microseconds(dtime_end - dtime_start)

            wall_clock_human = (
                timedelta_to_string(wall_clock_time) if wall_clock_time.seconds < 500 else f"{wall_clock_time.total_seconds()}s"
            )

            id: uuid.UUID | None = None

            if persist_profile:
                id = log_task_profile_to_database(task.__name__, dtime_start, dtime_end)

            id_msg: str = ""

            if link_tracing:
                id_msg = f"({get_id_profile_url(id)})" if id else ""

            # argument string
            method_args_string: str = ""

            if include_args:
                args_string = ", ".join([f"'{i}'" for i in args]) if args else ""
                kwargs_string = ", ".join(f"{key}={parse_kwargs_value(value)}" for key, value in kwargs.items())

                if args_string and kwargs_string:
                    args_string += ", "

                method_args_string = f"({args_string}{kwargs_string})"

            profile_message = f"[{settings.env}]{id_msg} `{task.__name__}{method_args_string}` in " f"{wall_clock_human} "

            if send_slack:
                slack_message(profile_message)

            logger.info(profile_message)

            return run_task_output

        return _task_profile_wrapper

    return profile_task_decorator


@profile_task(send_slack=True)
def test_task(message: str | None = None) -> None:
    """Test task"""
    time.sleep(random.randint(1, 3))
    print(f"complete: {message}")


if __name__ == "__main__":
    test_task("test mess")
