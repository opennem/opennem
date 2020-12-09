#!/usr/bin/env python
"""


"""
import logging
from urllib.parse import urljoin

import requests
from scrapy import spiderloader
from scrapy.utils import project

from opennem.settings import settings

SCRAPYD_SERVER = "https://scrapyd.dev.opennem.org.au/"

logger = logging.getLogger("spider_queue")


def get_spiders():
    settings = project.get_project_settings()
    spider_loader = spiderloader.SpiderLoader.from_settings(settings)
    spiders = spider_loader.list()
    classes = [spider_loader.load(name) for name in spiders]

    return [str(i.name) for i in classes]


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

    # print(spiders)

    for s in spiders:
        if "historic" in s:
            add_spider(s)

    # add_spider("au.nem.latest.price")


if __name__ == "__main__":
    queue_spider()
