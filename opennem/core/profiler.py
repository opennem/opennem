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

from humanize import naturaldelta
from sqlalchemy import event as sa_event
from sqlalchemy import text as sql_text
from sqlalchemy.engine import Engine

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db import get_database_engine

logger = logging.getLogger("opennem.profiler")


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


def log_task_profile_to_database(task_name: str, time_start: datetime, time_end: datetime) -> str:
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


def profile_task(send_slack: bool = False, profile_sql: bool = False, persist_profile: bool = True) -> Callable:
    """Profile a task and log the time taken to run it"""

    if profile_sql:
        bind_sqlalchemy_events()

    def profile_task_decorator(task: Any, *args: Any, **kwargs: Any) -> Any:

        time_start = time.perf_counter()
        dtime_start = datetime.now()

        @functools.wraps(task)
        def _task_profile_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for the task"""
            logger.info(f"Running task: {task.__name__}")

            run_task_output = task(*args, **kwargs)

            dtime_end = datetime.now()

            human_interval = naturaldelta(dtime_end - dtime_start)
            completed_time_seconds = round(time.perf_counter() - time_start)

            id: str | None = None

            if persist_profile:
                id = log_task_profile_to_database(task.__name__, dtime_start, dtime_end)

            id_msg = f"[{id}]" if id else ""

            profile_message = (
                f"[{settings.env}] Completed task {task.__name__} in {human_interval} [perf:{completed_time_seconds}] {id_msg}"
            )

            if send_slack:
                slack_message(profile_message)

            logger.info(profile_message)

            return run_task_output

        return _task_profile_wrapper

    return profile_task_decorator


@profile_task()
def test_task(message: str | None = None) -> None:
    """Test task"""
    time.sleep(random.randint(1, 3))
    print(f"complete: {message}")


if __name__ == "__main__":
    test_task("test mess")
