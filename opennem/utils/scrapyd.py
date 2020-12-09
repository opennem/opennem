#!/usr/bin/env python
"""
Srapyd control methods

"""
import logging
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests

from opennem.settings import settings
from opennem.utils.scrapy import get_spiders

logger = logging.getLogger("scrapyd.client")


def get_jobs() -> Dict[str, Any]:
    job_url = urljoin(
        settings.scrapyd_url,
        "listjobs.json?project={}".format(settings.scrapyd_project_name),
    )

    jobs = requests.get(job_url).json()

    return jobs


def job_cancel(id: str) -> bool:
    cancel_job_url = urljoin(settings.scrapyd_url, "cancel.json")

    r = requests.post(cancel_job_url, data={"project": "opennem", "job": id})

    resp = r.json()

    if resp["status"] == "error":
        logger.error("Error: {}".format(resp["message"]))
        return False

    logger.info("Cancelled job: {}".format(resp["jobid"]))

    return True


def job_schedule(spider_name: str) -> bool:
    schedule_url = urljoin(settings.scrapyd_url, "schedule.json")

    r = requests.post(
        schedule_url, data={"project": "opennem", "spider": spider_name}
    )

    if not r.ok:
        logger.error("Error: {}".format(r.status_code))
        return False

    resp = r.json()

    if resp["status"] == "error":
        logger.error("Error: {}".format(resp["message"]))
        return False

    logger.info(
        "Queued spider {} with task: {}".format(spider_name, resp["jobid"])
    )

    return True


def job_cancel_state(state: str = "pending") -> bool:
    jobs = get_jobs()

    if state not in jobs:
        logger.info("Invalid state or no jobs in state {}".format(state))
        return False

    pending_jobs = jobs[state]

    for job in pending_jobs:
        job_id = job["id"]
        logger.info("Cancelling {}".format(job_id))
        job_cancel(job_id)

    return True


def job_schedule_all(matches: str = None) -> List[str]:
    spiders = get_spiders()

    spider_scheduled = []

    for s in spiders:
        if matches and matches not in s:
            continue
        job_schedule(s)
        spider_scheduled.append(s)

    return spider_scheduled
