#!/usr/bin/env python
"""


"""
import logging
from typing import List
from urllib.parse import urljoin

import requests
from scrapy import spiderloader
from scrapy.utils import project

from opennem.settings import settings

SCRAPYD_SERVER = "https://scrapyd.dev.opennem.org.au/"

logger = logging.getLogger("spider_queue")


def get_spiders() -> List[str]:
    scrapy_settings = project.get_project_settings()
    spider_loader = spiderloader.SpiderLoader.from_settings(scrapy_settings)
    spiders = spider_loader.list()
    classes = [spider_loader.load(name) for name in spiders]

    return [str(i.name) for i in classes]


def get_jobs() -> List[str]:
    job_url = urljoin(SCRAPYD_SERVER, "listjobs.json?project=opennem")

    jobs = requests.get(job_url).json()

    return jobs


def cancel_job(id: str) -> bool:
    cancel_job_url = urljoin(SCRAPYD_SERVER, "cancel.json")

    r = requests.post(cancel_job_url, data={"project": "opennem", "job": id})

    resp = r.json()

    if resp["status"] == "error":
        logger.error("Error: {}".format(resp["message"]))
        return False

    logger.info("Cancelled job: {}".format(resp["jobid"]))

    return True


def add_spider(spider_name: str) -> bool:
    schedule_url = urljoin(SCRAPYD_SERVER, "schedule.json")

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


def cancel_pending():
    jobs = get_jobs()

    pending_jobs = jobs["pending"]

    for job in pending_jobs:
        job_id = job["id"]
        logger.info("Cancelling {}".format(job_id))
        cancel_job(job_id)


def add_spider(spider_name: str) -> bool:
    schedule_url = urljoin(SCRAPYD_SERVER, "schedule.json")

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


def queue_spider():
    spiders = get_spiders()

    for s in spiders:
        if "current" in s and s != "au.mms.archive":
            add_spider(s)


if __name__ == "__main__":
    queue_spider()
