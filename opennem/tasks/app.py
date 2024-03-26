import asyncio
import logging

from asgiref.sync import async_to_sync
from celery import Celery

from opennem import settings

logger = logging.getLogger("openne.tasks.app")

app = Celery("tasks", broker=settings.celery_broker, backend=settings.celery_backend)
app.conf.timezone = "Australia/Brisbane"  # @NOTE Brisbane has no DST so is +10


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(30.0, task_per_interval_check.apply_async(), name="per interval check every 30s")

    # Calls test('world') every 30 seconds
    # sender.add_periodic_task(30.0, test.s("world"), expires=10)

    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     test.s('Happy Mondays!'),
    # )


@app.task(async_mode="thread")
def task_per_interval_check() -> None:
    logger.info("Running per interval check")
    async_to_sync(asyncio.sleep)(1)
    logger.info("Slept 1s")


if __name__ == "__main__":
    task_per_interval_check.apply_async()
