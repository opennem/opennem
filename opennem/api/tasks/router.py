import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from starlette import status

from opennem.api.export.map import PriorityType, priority_from_name
from opennem.api.export.tasks import export_energy, export_power
from opennem.workers.scheduler import huey

logger = logging.getLogger(__name__)

router = APIRouter()


@huey.task()
def export_energy_task(priority: PriorityType, latest: bool) -> None:
    export_energy(priority=priority, latest=latest)


@huey.task()
def export_power_task(priority: PriorityType) -> None:
    export_power(priority=priority)


@router.get("/worker/task")
def worker_task(
    name: str = Query(None, description="type of task"),
    priority_name: str = Query("live", description="Task priority"),
    latest: bool = Query(False, description="Only run the latest"),
) -> Any:
    priority = priority_from_name(priority_name)

    task = None

    if name == "energy":
        task = export_energy_task.schedule(kwargs={"priority": priority, "latest": latest}, delay=1)
    elif name == "power":
        task = export_power_task.schedule({"priority": priority, "latest": latest}, delay=1)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find task type",
        )

    return task.id


@router.get("/worker/queue")
def worker_queue() -> Any:
    res = huey.all_results().keys()

    return [i.decode("utf-8") for i in res]
