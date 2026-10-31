"""Worker maintenance guard (#782): crons and on-demand jobs skip cleanly while MAINTENANCE_MODE is on.

Applied centrally to WorkerSettings.cron_jobs/functions, so a skipped job logs one info line, returns success
(no retry, no Sentry event) and touches nothing. The flag is read on every call.
"""

import dataclasses
import functools
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from arq.cron import CronJob
from arq.worker import Function

from opennem.core.maintenance import is_maintenance_mode

logger = logging.getLogger("opennem.tasks.maintenance")

_GUARDED_ATTR = "__maintenance_guarded__"


def maintenance_guard(name: str, coroutine: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Wrap a job coroutine: skip (return None) while maintenance is on, otherwise run it unchanged."""
    if getattr(coroutine, _GUARDED_ATTR, False):
        return coroutine

    @functools.wraps(coroutine)
    async def guarded(ctx: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        if is_maintenance_mode():
            logger.info(f"maintenance mode: skipping {name}")
            return None
        return await coroutine(ctx, *args, **kwargs)

    setattr(guarded, _GUARDED_ATTR, True)
    return guarded


def guard_jobs[JobT: (CronJob, Function)](jobs: Sequence[JobT]) -> list[JobT]:
    """Wrap every cron/function's coroutine, keeping arq's name (and so job ids and enqueue-by-name) unchanged."""
    return [dataclasses.replace(job, coroutine=maintenance_guard(job.name, job.coroutine)) for job in jobs]
