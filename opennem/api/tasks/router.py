import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.utils.scrapyd import get_jobs, job_schedule_all

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scrapy/task")
def scrapy_task(
    name: str = Query(None, description="name of spider to queue")
) -> List[str]:
    return job_schedule_all(name)


@router.get("/scrapy/queue")
def scrapy_queue() -> Dict[str, Any]:
    resp = get_jobs()
    return resp
